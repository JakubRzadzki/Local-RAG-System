"""``/api/documents`` endpoints."""

from typing import Annotated

from fastapi import APIRouter, File, Form, Response, UploadFile, status

from local_rag_system.dependencies import IngestionServiceDep, SettingsDep
from local_rag_system.schemas.documents import ChunkPreviewOut, DocumentOut, DocumentPreviewOut

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
async def list_documents(service: IngestionServiceDep) -> list[DocumentOut]:
    """List all indexed documents, newest first."""
    return [DocumentOut.model_validate(d) for d in await service.list_documents()]


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    service: IngestionServiceDep,
    settings: SettingsDep,
    file: Annotated[UploadFile, File(description="TXT, MD or PDF file")],
    chunk_size: Annotated[int | None, Form(ge=100, le=4000)] = None,
    chunk_overlap: Annotated[int | None, Form(ge=0, le=1000)] = None,
) -> DocumentOut:
    """Upload a file, split it into chunks and index their embeddings."""
    document = await service.ingest(
        filename=file.filename or "untitled",
        content_type=file.content_type or "application/octet-stream",
        data=await file.read(),
        chunk_size=chunk_size or settings.default_chunk_size,
        chunk_overlap=(settings.default_chunk_overlap if chunk_overlap is None else chunk_overlap),
    )
    return DocumentOut.model_validate(document)


@router.get("/{document_id}/preview", response_model=DocumentPreviewOut)
async def preview_document(document_id: int, service: IngestionServiceDep) -> DocumentPreviewOut:
    """Return a document's stored chunks so the UI can preview its content."""
    document, chunks = await service.get_preview(document_id)
    return DocumentPreviewOut(
        document=DocumentOut.model_validate(document),
        chunks=[
            ChunkPreviewOut(chunk_index=c.chunk_index, page=c.page, content=c.content)
            for c in chunks
        ],
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: int, service: IngestionServiceDep) -> Response:
    """Delete a document together with its chunks."""
    await service.delete_document(document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
