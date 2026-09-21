# Ultrasound Research Guide

Pipeline: IMAGE → IMPORT → VALIDATION → QUALITY → PREPROCESSING → ANNOTATION → SEGMENTATION → FEATURE EXTRACTION → MODEL → UNCERTAINTY → EXPLANATION → REPORT.

Preferred infrastructure: pydicom for DICOM interoperability and MONAI/TorchIO/nnU-Net/MONAI Label where the actual research workflow requires them.

No validated ovarian model = MODEL_UNAVAILABLE or INSUFFICIENT_DATA. Do not fabricate ovarian volume, follicle/cyst count, probability, sensitivity, specificity or segmentation accuracy.
