from typing import Union, Dict, Any, List, Generic, Type
import re
from sqlalchemy import and_, UniqueConstraint, Index
import psycopg2
from sqlalchemy.exc import IntegrityError
from db import db
from model import ModelType, ModelForTest


class Repository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model: Type[ModelType] = model

    def _to_model(self, data: Union[ModelType, Dict[str, Any]]) -> ModelType:
        """Failsafe helper method to convert a dict or model to a model"""
        if isinstance(data, dict):
            model = self.model(**data)
        else:
            model = data

        return model

    def _is_matching_unique_constraint_violation(self, e) -> bool:
        if not isinstance(e.orig, psycopg2.errors.UniqueViolation):
            return False

        if not e.args:
            return False

            # Should be okay to parse the error message from postgres - this is also done e.g. by this project
            # https://github.com/openstack/oslo.db/blob/1b48a34bd11f40fc516995ed693d193f28c80b25/oslo_db/sqlalchemy/exc_filters.py
        pattern = r"Key\s+\((?P<key>.*)\)=\((?P<value>.*)\)\s+already\s+exists.*$"
        m = re.search(pattern, str(e.args))

        if not m:
            return False

        keys = m.groupdict().get("key")

        if not keys:
            return False

        keys = keys.split(", ")

        unique_column_groups = [
            c.columns.keys()
            for c in self.model.__table__.constraints  # type: ignore
            if isinstance(c, UniqueConstraint)
        ] + [
            i.columns.keys()
            for i in self.model.__table__.indexes  # type: ignore
            if isinstance(i, Index) and i.unique
        ]

        is_true_unique_key_violation = any(
            all(k in columns for k in keys) for columns in unique_column_groups
        )

        return is_true_unique_key_violation

    def _merge_models(
        self, existing_model: ModelType, update_model: ModelType
    ) -> ModelType:
        model = update_model
        model.id = existing_model.id

        # merge is not calling onupdate https://stackoverflow.com/a/34013607/8301780
        model.updated_at = db.func.now()
        return db.session.merge(model)

    def update_or_create_naive(
        self,
        data: Union[ModelType, Dict[str, Any]],
        key_columns: List[str],
    ):
        create_data_model = self._to_model(data)

        filters = [
            getattr(self.model, k) == getattr(create_data_model, k) for k in key_columns
        ]

        query = db.session.query(self.model).filter(and_(*filters))
        existing_model = query.one_or_none()

        if existing_model:
            create_data_model.id = existing_model.id
            db.session.merge(create_data_model)
        else:
            db.session.add(create_data_model)

        db.session.commit()

    def update_or_create(
        self,
        data: Union[ModelType, Dict[str, Any]],
        key_columns: List[str],
    ) -> ModelType:
        """
        Creates or updates the model

        :param data: Either a dict or a model object
        :param key_columns: Columns which indicate the unique key(s) of the model, used to query the model to update
        :return: The ModelType object that was updated or created
        """
        create_data_model = self._to_model(data)

        filters = [
            getattr(self.model, k) == getattr(create_data_model, k) for k in key_columns
        ]
        query = db.session.query(self.model).filter(and_(*filters))
        existing_model = query.one_or_none()

        checkpoint = db.session.begin_nested()

        if existing_model:
            model = self._merge_models(existing_model, create_data_model)
        else:
            model = create_data_model
            db.session.add(model)

        try:
            # Attempt to upsert in a nested transaction
            checkpoint.commit()
        except IntegrityError as e:
            # Catching the constraint violation in case of a race condition
            # which can happen when transaction A attempts to create the model
            # while transaction B just did create it
            # in which case we rollback the attempt, and then re-try with a merge
            checkpoint.rollback()

            # we only re-try if it failed for the right reason
            if not self._is_matching_unique_constraint_violation(e):
                raise e

            existing_model = query.one()
            model = self._merge_models(existing_model, create_data_model)

        # commit the outer transaction
        db.session.commit()
        return model


test_repository = Repository[ModelForTest](ModelForTest)
