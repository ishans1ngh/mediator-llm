from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import Dict
from pathlib import Path
from backend.config import UPLOAD_DIR, DEMO_MODE
from backend.mri.unet import run_unet_segmentation
from backend.mri.resnet import extract_resnet_features
import uuid
import shutil

router = APIRouter(prefix="/mri", tags=["mri"])


@router.post("/upload")
async def upload_mri(
    t1: UploadFile = File(...),
    t1ce: UploadFile = File(...),
    t2: UploadFile = File(...),
    flair: UploadFile = File(...),
):
    """
    Upload the four MRI modalities required by the BraTS model.
    """

    files = {
        "t1": t1,
        "t1ce": t1ce,
        "t2": t2,
        "flair": flair,
    }

    try:
        file_id = str(uuid.uuid4())
        saved_files = {}

        for modality, file in files.items():

            filename = file.filename

            if not filename:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing filename for {modality}",
                )

            if not (
                filename.endswith(".nii")
                or filename.endswith(".nii.gz")
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"{modality} must be a .nii "
                        "or .nii.gz file"
                    ),
                )

            file_path = (
                UPLOAD_DIR /
                f"{file_id}_{modality}_{filename}"
            )

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(
                    file.file,
                    buffer,
                )

            if file_path.stat().st_size == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"{modality} file is empty",
                )

            saved_files[modality] = str(file_path)

        return {
            "file_id": file_id,
            "status": "uploaded",
            "modalities": saved_files,
            "demo_mode": DEMO_MODE,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}",
        )


@router.post("/analyze")
async def analyze_mri(
    file_id: str = Query(..., description="File ID from upload endpoint"),
):
    """
    Analyze a previously uploaded 4-modality MRI.
    """

    try:

        # ---------------------------------
        # Find uploaded modality files
        # ---------------------------------

        modality_paths: Dict[str, str] = {}

        for modality in [
            "t1",
            "t1ce",
            "t2",
            "flair",
        ]:

            matches = list(
                UPLOAD_DIR.glob(
                    f"{file_id}_{modality}_*"
                )
            )

            if not matches:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Missing uploaded modality: "
                        f"{modality}"
                    ),
                )

            modality_paths[modality] = str(
                matches[0]
            )

        # ---------------------------------
        # Validate dimensions
        # ---------------------------------

        import nibabel as nib

        shapes = {}

        for modality, path in modality_paths.items():

            img = nib.load(path)
            shapes[modality] = list(img.shape)

        if len(
            {
                tuple(shape)
                for shape in shapes.values()
            }
        ) != 1:

            raise HTTPException(
                status_code=400,
                detail={
                    "error": "MRI dimensions do not match",
                    "shapes": shapes,
                },
            )

        # ---------------------------------
        # Prepare MRI data
        # ---------------------------------

        preprocessing_result = {
            "status": "success",
            "modalities": modality_paths,
            "shapes": shapes,
            "demo_mode": DEMO_MODE,
        }

        # ---------------------------------
        # Run MONAI segmentation
        # ---------------------------------

        segmentation_result = (
            run_unet_segmentation(
                preprocessing_result
            )
        )

        # ---------------------------------
        # Optional ResNet features
        # ---------------------------------

        feature_result = {
            "feature_vector_available": False,
            "feature_dimension": None,
            "status": "not_configured",
            "note": "Optional ResNet feature extraction is not configured. MRI segmentation is performed using MONAI SegResNet."
        }

        return {
            "file_id": file_id,
            "preprocessing": preprocessing_result,
            "segmentation": segmentation_result,
            "features": feature_result,
            "demo_mode": DEMO_MODE,
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}",
        )