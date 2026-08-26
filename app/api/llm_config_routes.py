from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.llm_config import LLMConfig
from app.schemas.llm_config import LLMConfigCreate, LLMConfigResponse


router = APIRouter(
    prefix="/llm-configs",
    tags=["LLM Configs"],
)


@router.post("/", response_model=LLMConfigResponse)
def create_config(
    data: LLMConfigCreate,
    db: Session = Depends(get_db),
):
    config = LLMConfig(**data.model_dump())

    db.add(config)
    db.commit()
    db.refresh(config)

    return config


@router.get("/", response_model=list[LLMConfigResponse])
def list_configs(
    db: Session = Depends(get_db),
):
    return (
        db.query(LLMConfig)
        .order_by(LLMConfig.created_at.desc())
        .all()
    )


@router.get("/{config_id}", response_model=LLMConfigResponse)
def get_config(
    config_id: UUID,
    db: Session = Depends(get_db),
):
    config = (
        db.query(LLMConfig)
        .filter(LLMConfig.id == config_id)
        .first()
    )

    if not config:
        raise HTTPException(404, "LLM config not found")

    return config


@router.put("/{config_id}", response_model=LLMConfigResponse)
def update_config(
    config_id: UUID,
    data: LLMConfigCreate,
    db: Session = Depends(get_db),
):
    config = (
        db.query(LLMConfig)
        .filter(LLMConfig.id == config_id)
        .first()
    )

    if not config:
        raise HTTPException(404, "LLM config not found")

    for key, value in data.model_dump().items():
        setattr(config, key, value)

    db.commit()
    db.refresh(config)

    return config


@router.delete("/{config_id}")
def delete_config(
    config_id: UUID,
    db: Session = Depends(get_db),
):
    config = (
        db.query(LLMConfig)
        .filter(LLMConfig.id == config_id)
        .first()
    )

    if not config:
        raise HTTPException(404, "LLM config not found")

    db.delete(config)
    db.commit()

    return {"message": "LLM config deleted successfully"}