import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from backend.database import (
    get_categories, get_category_by_id, get_category_by_name,
    create_category, update_category, delete_category, duplicate_category,
    get_prompt_templates, get_prompt_template_by_id,
    create_prompt_template, update_prompt_template, delete_prompt_template
)

router = APIRouter(prefix="/api/categories", tags=["categories"])
logger = logging.getLogger("cosmos.categories")

class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=60)
    description: Optional[str] = ""
    accent_color: str = Field(..., pattern=r"^#[0-9a-fA-F]{6}$")
    text_color: Optional[str] = None
    icon: Optional[str] = "🎯"
    theme_label: Optional[str] = None
    visual_style: Optional[str] = "Cinematic Drone"
    default_language: Optional[str] = "hindi" # "hindi", "hinglish", "english", "custom"
    default_duration: Optional[int] = 52
    caption_position_y: Optional[float] = 76.0
    caption_font_size: Optional[int] = 70
    caption_highlight_color: Optional[str] = None
    prompt_template_id: Optional[str] = None
    custom_prompt_instructions: Optional[str] = ""
    is_default: Optional[bool] = False
    is_enabled: Optional[bool] = True

class CategoryUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=60)
    description: Optional[str] = None
    accent_color: Optional[str] = None
    text_color: Optional[str] = None
    icon: Optional[str] = None
    theme_label: Optional[str] = None
    visual_style: Optional[str] = None
    default_language: Optional[str] = None
    default_duration: Optional[int] = None
    caption_position_y: Optional[float] = None
    caption_font_size: Optional[int] = None
    caption_highlight_color: Optional[str] = None
    prompt_template_id: Optional[str] = None
    custom_prompt_instructions: Optional[str] = None
    is_default: Optional[bool] = None
    is_enabled: Optional[bool] = None
    order_index: Optional[int] = None

class DeleteCategoryRequest(BaseModel):
    reassign_to_id: Optional[str] = None
    archive_only: Optional[bool] = False

class PromptTemplateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    description: Optional[str] = ""
    category_id: Optional[str] = None
    language: Optional[str] = "hindi"
    system_prompt: Optional[str] = ""
    user_prompt_template: Optional[str] = ""
    is_global: Optional[bool] = True

# ----------------------------------------------------
# CATEGORIES ENDPOINTS
# ----------------------------------------------------
@router.get("")
def list_categories(include_disabled: bool = Query(False)):
    """Returns all active or all categories with their theme tokens."""
    cats = get_categories(include_disabled=include_disabled)
    return {"categories": cats, "total": len(cats)}

@router.get("/{cat_id}")
def get_category(cat_id: str):
    cat = get_category_by_id(cat_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    return cat

@router.post("")
def create_new_category(req: CategoryCreateRequest):
    try:
        data = req.dict()
        created = create_category(data)
        return {"status": "created", "category": created}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating category: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{cat_id}")
def update_existing_category(cat_id: str, req: CategoryUpdateRequest):
    try:
        data = {k: v for k, v in req.dict().items() if v is not None}
        updated = update_category(cat_id, data)
        return {"status": "updated", "category": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating category: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{cat_id}")
def remove_category(cat_id: str, req: Optional[DeleteCategoryRequest] = None):
    try:
        archive_only = req.archive_only if req else False
        reassign_to_id = req.reassign_to_id if req else None
        result = delete_category(cat_id, reassign_to_id=reassign_to_id, archive_only=archive_only)
        return {"status": "success", "result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting category: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{cat_id}/duplicate")
def duplicate_existing_category(cat_id: str):
    try:
        dup = duplicate_category(cat_id)
        return {"status": "duplicated", "category": dup}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/data/export")
def export_categories_data():
    cats = get_categories(include_disabled=True)
    tpls = get_prompt_templates()
    return {
        "export_version": "1.0",
        "categories": cats,
        "prompt_templates": tpls
    }

@router.post("/data/import")
def import_categories_data(payload: Dict[str, Any]):
    imported_cats = 0
    imported_tpls = 0
    
    # Import prompt templates first
    for tpl in payload.get("prompt_templates", []):
        try:
            if not get_prompt_template_by_id(tpl.get("id", "")):
                create_prompt_template(tpl)
                imported_tpls += 1
        except Exception:
            pass

    # Import categories
    for cat in payload.get("categories", []):
        try:
            existing = get_category_by_id(cat.get("id", "")) or get_category_by_name(cat.get("name", ""))
            if not existing:
                create_category(cat)
                imported_cats += 1
            else:
                # Update existing
                update_category(existing["id"], cat)
                imported_cats += 1
        except Exception as e:
            logger.warning(f"Failed to import category: {e}")

    return {
        "status": "success",
        "imported_categories": imported_cats,
        "imported_templates": imported_tpls
    }

# ----------------------------------------------------
# PROMPT TEMPLATES ENDPOINTS
# ----------------------------------------------------
@router.get("/templates/all")
def list_prompt_templates(category_id: Optional[str] = Query(None)):
    tpls = get_prompt_templates(category_id=category_id)
    return {"templates": tpls}

@router.get("/templates/{tpl_id}")
def get_single_template(tpl_id: str):
    tpl = get_prompt_template_by_id(tpl_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found.")
    return tpl

@router.post("/templates")
def create_template(req: PromptTemplateRequest):
    try:
        created = create_prompt_template(req.dict())
        return {"status": "created", "template": created}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/templates/{tpl_id}")
def update_template(tpl_id: str, req: PromptTemplateRequest):
    try:
        updated = update_prompt_template(tpl_id, req.dict())
        return {"status": "updated", "template": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/templates/{tpl_id}")
def remove_template(tpl_id: str):
    try:
        return delete_prompt_template(tpl_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
