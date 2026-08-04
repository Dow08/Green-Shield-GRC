from fastapi import APIRouter
from . import crud
from . import exports
from . import snapshots_routes
from . import copilot_routes

router = APIRouter()
router.include_router(crud.router)
router.include_router(exports.router)
router.include_router(snapshots_routes.router)
router.include_router(copilot_routes.router)
