"""
Wiki Routes - REST API for wiki pages
Provides CRUD operations and search capabilities
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from storage.wiki_db import get_wiki_db, WikiPage

router = APIRouter(prefix="/wiki", tags=["wiki"])


class WikiPageCreate(BaseModel):
    slug: str
    title: str
    content: str = ""
    entity_ids: Optional[List[str]] = None


class WikiPageUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    synthesized_content: Optional[str] = None


class WikiPageResponse(BaseModel):
    id: str
    slug: str
    title: str
    content: Optional[str]
    entity_ids: Optional[List[str]]
    created_at: Optional[str]
    updated_at: Optional[str]
    last_synthesis: Optional[str]
    contradiction_count: int
    version: int
    synthesized_content: Optional[str]

    @classmethod
    def from_wiki_page(cls, page: WikiPage):
        return cls(**vars(page))


class WikiBacklinkResponse(BaseModel):
    from_slug: str
    to_slug: str
    context: Optional[str]
    created_at: Optional[str]


class RelatedPagesResponse(BaseModel):
    slug: str
    pages: List[WikiPageResponse]


class SearchResultsResponse(BaseModel):
    query: str
    total: int
    pages: List[WikiPageResponse]


@router.post("", response_model=WikiPageResponse)
async def create_wiki_page(page: WikiPageCreate):
    """Create a new wiki page"""
    db = get_wiki_db()

    # Check if page already exists
    existing = db.get_page(page.slug)
    if existing:
        raise HTTPException(status_code=409, detail=f"Wiki page '{page.slug}' already exists")

    try:
        created_page = db.create_page(
            slug=page.slug,
            title=page.title,
            content=page.content,
            entity_ids=page.entity_ids
        )
        return WikiPageResponse.from_wiki_page(created_page)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create wiki page: {str(e)}")


@router.get("/{slug}", response_model=WikiPageResponse)
async def get_wiki_page(slug: str):
    """Get a wiki page by slug"""
    db = get_wiki_db()
    page = db.get_page(slug)

    if not page:
        raise HTTPException(status_code=404, detail=f"Wiki page '{slug}' not found")

    return WikiPageResponse.from_wiki_page(page)


@router.put("/{slug}", response_model=WikiPageResponse)
async def update_wiki_page(slug: str, update: WikiPageUpdate):
    """Update an existing wiki page"""
    db = get_wiki_db()

    # Check page exists
    existing = db.get_page(slug)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Wiki page '{slug}' not found")

    try:
        updated_page = db.update_page(
            slug=slug,
            content=update.content,
            title=update.title,
            synthesized_content=update.synthesized_content
        )
        return WikiPageResponse.from_wiki_page(updated_page)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update wiki page: {str(e)}")


@router.delete("/{slug}")
async def delete_wiki_page(slug: str):
    """Delete a wiki page"""
    db = get_wiki_db()

    if not db.get_page(slug):
        raise HTTPException(status_code=404, detail=f"Wiki page '{slug}' not found")

    success = db.delete_page(slug)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete wiki page")

    return {"status": "deleted", "slug": slug}


@router.get("/search", response_model=SearchResultsResponse)
async def search_wiki(q: str = Query(..., min_length=1)):
    """Search wiki pages by title and content"""
    db = get_wiki_db()

    try:
        results = db.search_pages(q)
        return SearchResultsResponse(
            query=q,
            total=len(results),
            pages=[WikiPageResponse.from_wiki_page(page) for page in results]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Search failed: {str(e)}")


@router.get("/{slug}/related", response_model=RelatedPagesResponse)
async def get_related_pages(slug: str):
    """Get pages related to a given page"""
    db = get_wiki_db()

    # Check page exists
    page = db.get_page(slug)
    if not page:
        raise HTTPException(status_code=404, detail=f"Wiki page '{slug}' not found")

    try:
        related = db.get_related_pages(slug)
        return RelatedPagesResponse(
            slug=slug,
            pages=[WikiPageResponse.from_wiki_page(p) for p in related]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get related pages: {str(e)}")


@router.get("/{slug}/backlinks")
async def get_wiki_backlinks(slug: str):
    """Get pages that link TO this page"""
    db = get_wiki_db()

    # Check page exists
    if not db.get_page(slug):
        raise HTTPException(status_code=404, detail=f"Wiki page '{slug}' not found")

    try:
        backlinks = db.get_backlinks(slug)
        return {
            "slug": slug,
            "backlinks": [
                {"from_slug": bl.from_slug, "to_slug": bl.to_slug, "context": bl.context}
                for bl in backlinks
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get backlinks: {str(e)}")


@router.post("/{from_slug}/link/{to_slug}")
async def create_backlink(from_slug: str, to_slug: str, context: Optional[str] = None):
    """Create a backlink between two pages"""
    db = get_wiki_db()

    # Check both pages exist
    if not db.get_page(from_slug):
        raise HTTPException(status_code=404, detail=f"Wiki page '{from_slug}' not found")
    if not db.get_page(to_slug):
        raise HTTPException(status_code=404, detail=f"Wiki page '{to_slug}' not found")

    try:
        backlink = db.add_backlink(from_slug, to_slug, context)
        return {
            "from_slug": backlink.from_slug,
            "to_slug": backlink.to_slug,
            "context": backlink.context,
            "created_at": backlink.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create backlink: {str(e)}")


@router.get("/entity/{entity_id}")
async def get_entity_wiki_pages(entity_id: str):
    """Get all wiki pages for a specific entity"""
    db = get_wiki_db()

    try:
        pages = db.get_pages_for_entity(entity_id)
        return {
            "entity_id": entity_id,
            "pages": [WikiPageResponse.from_wiki_page(p) for p in pages],
            "total": len(pages)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get entity pages: {str(e)}")


@router.get("", response_model=dict)
async def list_wiki_pages(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    """List all wiki pages with pagination"""
    db = get_wiki_db()

    try:
        pages = db.get_all_pages(limit=limit, offset=offset)
        return {
            "pages": [WikiPageResponse.from_wiki_page(p) for p in pages],
            "total": len(pages),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to list pages: {str(e)}")
