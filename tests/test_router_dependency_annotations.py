from typing import Annotated, get_args, get_origin, get_type_hints

import pytest
from fastapi.params import Depends

from app.modules.companies import router as companies_router
from app.modules.membership import router as membership_router
from app.modules.users import router as users_router


@pytest.mark.parametrize(
    ("endpoint", "parameter_name"),
    [
        (companies_router.get_registration_options, "db"),
        (membership_router.get_reviews, "admin_user"),
        (membership_router.get_reviews, "db"),
        (membership_router.approve_user_review, "admin_user"),
        (membership_router.approve_user_review, "db"),
        (membership_router.block_user_review, "admin_user"),
        (membership_router.block_user_review, "db"),
        (membership_router.sync_clickup_reviews, "admin_user"),
        (membership_router.sync_clickup_reviews, "db"),
        (users_router.get_me, "user"),
        (users_router.put_me, "user"),
        (users_router.put_me, "db"),
        (users_router.put_my_company, "user"),
        (users_router.put_my_company, "db"),
        (users_router.list_favorites, "user"),
        (users_router.list_favorites, "db"),
        (users_router.add_fav, "user"),
        (users_router.add_fav, "db"),
        (users_router.remove_fav, "user"),
        (users_router.remove_fav, "db"),
    ],
)
def test_endpoint_dependencies_use_annotated(endpoint, parameter_name):
    annotation = get_type_hints(endpoint, include_extras=True)[parameter_name]

    assert get_origin(annotation) is Annotated
    dependency = get_args(annotation)[1]
    assert isinstance(dependency, Depends)
