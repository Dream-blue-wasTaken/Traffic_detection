YOLOv7 Vehicle Detection Fine-Tuning — Codex Implementation Specification

0. Objective

Build a reproducible Google Colab project that fine-tunes the official YOLOv7 object detector on a small, domain-specific traffic dataset using an NVIDIA Tesla T4 GPU.


The target application is:



Given a traffic video, detect and classify road vehicles such as cars, motorcycles, buses, and trucks.



This is fine-tuning, not training from scratch.


Start from official pretrained YOLOv7 weights and adapt the model to the selected traffic dataset.



1. Important constraints

Hardware

Target environment:



Google Colab

NVIDIA Tesla T4

CUDA-enabled PyTorch

Do not assume an A100 or larger GPU.


Dataset size

Keep the dataset intentionally small.


Target:



150–200 training images/frames

30–50 validation images/frames

Optionally 30–50 held-out test images/frames


Do NOT download or process the entire BDD100K/AI City/etc. dataset.


The purpose is to demonstrate fine-tuning with a small domain-specific dataset.


Classes

Target classes:


0 = car
1 = motorcycle
2 = bus
3 = truck

If the chosen dataset uses different names or labels, write a conversion/mapping script rather than silently changing the intended class semantics.


If a dataset cannot provide motorcycle annotations, do NOT pretend it does. Either:



find a better dataset, or

clearly document the missing class and stop before training.


Training approach

Use:


Official pretrained YOLOv7
        ↓
small traffic dataset
        ↓
fine-tuned YOLOv7

Do not train from random initialization.



2. Primary repository

Use the official YOLOv7 implementation:


https://github.com/WongKinYiu/yolov7

Clone the repository in Colab rather than recreating YOLOv7 from scratch.


The implementation should remain as close as practical to the official repository.



3. First notebook section — environment

Create a notebook section that:



Checks the Python version.

Checks PyTorch version.

Checks CUDA availability.

Prints GPU name.

Confirms the GPU is a Tesla T4 when available.

Clones the official YOLOv7 repository.

Installs only the required dependencies.

Verifies that YOLOv7 can import successfully.


Example diagnostic output should include:


PyTorch version:
CUDA available:
CUDA version:
GPU:
GPU memory:

Do not hard-code assumptions about CUDA versions. Use the environment's installed CUDA/PyTorch versions.



4. Dataset acquisition

The implementation must support a small traffic dataset.


Prefer a dataset that contains real traffic imagery/video frames and annotations for:



car

motorcycle

bus

truck


Potential sources include:



BDD100K

AI City Challenge datasets

other legitimate public traffic datasets


Do NOT download an enormous dataset unnecessarily.


If the selected source is large, implement a deterministic sampling step that selects only the required number of images.


The selection should be reproducible using a fixed random seed.



5. Dataset selection strategy

Do NOT simply take 200 consecutive video frames.


That would produce many nearly identical images.


Instead, select diverse frames covering conditions such as:



normal traffic

dense traffic

motorcycles

buses/trucks

different vehicle scales

partial occlusion

different camera viewpoints

different lighting where available


A reasonable target:


Training:
150–200 images

Validation:
30–50 images

Test:
30–50 images if enough labeled data is available

The test set must not overlap with training or validation.


If source videos are available, avoid placing adjacent frames from the same short temporal segment into both train and validation/test.


Prefer splitting by video/sequence when possible.



6. Annotation conversion

YOLOv7 expects YOLO-format labels.


Each image should have a corresponding .txt file:


class_id x_center y_center width height

All coordinates must be normalized to [0, 1].


Example:


0 0.52 0.43 0.31 0.22

Implement a conversion script if the original dataset uses:



JSON

XML

CSV

another annotation format


The conversion must:



Map source classes to the four target classes.

Convert bounding boxes to YOLO format.

Skip unsupported classes.

Reject invalid bounding boxes.

Verify normalized coordinates.

Report class counts.



7. Dataset directory structure

Create:


dataset/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
│
└── labels/
    ├── train/
    ├── val/
    └── test/

If no test set is available, clearly document that and use only train/val.


Also create a dataset configuration file such as:


train: /content/.../dataset/images/train
val: /content/.../dataset/images/val

nc: 4

names:
  - car
  - motorcycle
  - bus
  - truck

Use absolute paths appropriate for Colab or generate the paths dynamically.


Do not hard-code /content paths in code that is intended to be reused outside Colab unless the notebook explicitly documents this.



8. Dataset validation BEFORE training

This is mandatory.


Create code that checks:



every image has a label file when expected

every label has a valid class ID

every bounding box has five values

coordinates are numeric

coordinates are within valid normalized ranges

width and height are > 0

no corrupted images

no duplicate filenames across splits

class distribution


Print a report such as:


TRAIN
Images: 180
Car instances: ...
Motorcycle instances: ...
Bus instances: ...
Truck instances: ...

VAL
Images: 40
...

TEST
Images: 40
...

If one class has zero examples, stop and report the problem instead of training a misleading four-class model.



9. Visualize annotations

Before training, randomly select approximately 9–12 training images and draw the bounding boxes and class names on them.


Display them in the notebook.


This is important for catching:



wrong class mappings

flipped coordinates

incorrect image dimensions

malformed annotations

boxes outside the image


Do not proceed to training until the visualizations look correct.



10. Download pretrained YOLOv7 weights

Use the official pretrained YOLOv7 weights from the official repository/release.


Prefer the standard YOLOv7 model for the first experiment.


Do not immediately use a huge YOLOv7 variant.


The first goal is:


YOLOv7 pretrained
→ fine-tune
→ evaluate

Record the exact weights filename and source URL in the notebook.



11. Baseline experiment

Before fine-tuning, run the pretrained YOLOv7 model on the validation/test images and, if possible, one traffic video.


Record baseline metrics/results.


At minimum collect:



precision

recall

mAP@0.50

mAP@0.50:0.95


Also record inference speed if practical:



FPS

latency per frame


Important:


The pretrained COCO model's class names must be mapped correctly when comparing against the four target classes.


If the pretrained model cannot directly produce one of the target classes, document that limitation rather than fabricating a baseline.



12. Fine-tuning

Fine-tune from pretrained YOLOv7 weights.


Start with a modest configuration appropriate for a T4.


Suggested starting point:


image size: 640
batch size: choose based on T4 memory
epochs: 30–50
workers: reasonable for Colab
optimizer: use YOLOv7's supported/default training configuration
pretrained weights: official YOLOv7 pretrained weights

Do not blindly force a batch size that causes CUDA out-of-memory.


If necessary:



lower batch size

use gradient accumulation only if compatible with the implementation

keep image size at 640 for the initial experiment


Save:



latest checkpoint

best checkpoint

training logs

loss curves

evaluation results



13. Training configuration

Create a clear configuration file/section containing:


model:
dataset:
weights:
img_size:
batch_size:
epochs:
seed:
device:

Use a fixed random seed where supported.


Document every non-default training parameter.


Do not modify YOLOv7 source code unless necessary.


If a source modification is necessary, explain exactly why.



14. Training monitoring

Plot or display:



box loss

objectness loss

classification loss

validation metrics

mAP


At minimum produce:


training loss vs epoch
validation mAP vs epoch

The notebook should make it possible to see whether the small dataset is overfitting.



15. Overfitting awareness

Because the dataset is intentionally small, explicitly check for overfitting.


Potential signs:


training loss ↓
training performance ↑
validation performance stagnates or ↓

Do not claim that fine-tuning improved generalization merely because training loss decreased.


The held-out validation/test performance is what matters.



16. Evaluation

Evaluate the fine-tuned model on the validation/test set.


Report:


Precision
Recall
mAP@0.50
mAP@0.50:0.95

Also provide per-class results if the implementation supports them:


car
motorcycle
bus
truck

Create a comparison table:


Model	Precision	Recall	mAP@0.50	mAP@0.50:0.95
Pretrained YOLOv7				
Fine-tuned YOLOv7				

Do not invent or estimate missing metrics.



17. Confusion/error analysis

Inspect representative predictions.


Create examples of:



correct car detection

correct motorcycle detection

missed motorcycle

car/motorcycle confusion

partially occluded vehicle

small distant vehicle

crowded traffic


Explain likely failure modes based on visible evidence.


Do not make unsupported claims.



18. Video inference

After fine-tuning, run the best checkpoint on a traffic video.


The pipeline should:


input video
    ↓
YOLOv7
    ↓
bounding boxes
    ↓
class + confidence
    ↓
annotated output video

Output should show:


car 0.91
motorcycle 0.87
truck 0.94

Also show FPS if practical.


Save the resulting video to a clear output path.



19. Tracking is a separate stage

Do NOT mix tracking into the first fine-tuning experiment.


First establish:


YOLOv7 = detection

Only after detection works should the project optionally add:


YOLOv7
   ↓
ByteTrack / DeepSORT / BoT-SORT
   ↓
persistent vehicle IDs

This separation is important because YOLOv7 itself is an object detector, not a multi-object tracker.



20. Optional second experiment — tracking

If time permits, add one tracker.


Recommended first choice:


ByteTrack

Then:


YOLOv7 detections
        ↓
ByteTrack
        ↓
vehicle IDs

Example output:


Car — ID 17
Motorcycle — ID 21
Truck — ID 25

Do not claim that YOLOv7 performs tracking by itself.



21. Reproducibility

The final notebook should make it possible to reproduce the experiment from a clean Colab runtime.


Include:



installation

repository clone

dataset preparation

dataset validation

visualization

pretrained baseline

fine-tuning

evaluation

video inference


Avoid manual steps wherever practical.


If a manual dataset download/license acceptance is unavoidable, clearly isolate that step.



22. File structure to produce

Aim for:


yolov7-vehicle-finetuning/
│
├── notebook/
│   └── yolov7_vehicle_finetuning.ipynb
│
├── scripts/
│   ├── prepare_dataset.py
│   ├── validate_dataset.py
│   ├── visualize_dataset.py
│   └── evaluate_results.py
│
├── data/
│   └── dataset.yaml
│
├── outputs/
│   ├── baseline/
│   ├── training/
│   ├── evaluation/
│   └── videos/
│
└── README.md

If the official YOLOv7 repository is cloned separately, do not unnecessarily duplicate its source files.



23. README requirements

Create a README explaining:


Project

"Fine-tuning YOLOv7 for Vehicle Detection in Traffic Videos"


Goal

Detect:



cars

motorcycles

buses

trucks


Hardware

Google Colab
NVIDIA Tesla T4

Dataset

Document:



dataset name

source

license/usage restrictions

number of training images

number of validation images

number of test images

class mapping

sampling strategy


Model

YOLOv7

Starting weights

Document the exact pretrained weights used.


Training

Document:



epochs

image size

batch size

seed

other important parameters


Results

Include the baseline vs fine-tuned table.


Limitations

Explicitly mention that the dataset is intentionally small and therefore the results should not be interpreted as state-of-the-art.



24. Research framing

The project should be framed as:



"Investigating the effect of domain-specific fine-tuning of YOLOv7 on vehicle detection in traffic videos using a small labeled dataset."



Potential research questions:



Does fine-tuning improve detection performance on the target traffic domain?

Which vehicle classes benefit most from fine-tuning?

How does a small training set affect generalization?

What failure cases remain after fine-tuning?


Do NOT claim that the project establishes a new state of the art.



25. Important implementation rules


Prefer the official YOLOv7 implementation.

Prefer pretrained weights.

Do not train from scratch.

Do not download the entire large dataset when only 150–200 training frames are required.

Keep train/validation/test splits independent.

Use reproducible sampling.

Verify annotations visually.

Never fabricate metrics.

Record actual runtime/FPS.

Do not silently change class definitions.

Keep detection and tracking as separate stages.

Make the notebook runnable from a clean Colab session.

Fail loudly when required data/classes are missing.

Explain errors instead of hiding them.



26. Expected final result

At the end, there should be a working pipeline:


                 TRAFFIC DATA
                      │
                      ▼
             150–200 training frames
                      │
                      ▼
             YOLO-format annotations
                      │
                      ▼
             pretrained YOLOv7
                      │
                      ▼
                fine-tuning
                      │
                      ▼
               best checkpoint
                      │
             ┌────────┴────────┐
             ▼                 ▼
        quantitative       traffic video
         evaluation             │
                                ▼
                       vehicle detection
                                │
                 ┌──────────────┼──────────────┐
                 ▼              ▼              ▼
               CAR        MOTORCYCLE          BUS/TRUCK

The final deliverables should include:



working Colab notebook

prepared small dataset or reproducible dataset-preparation script

fine-tuned .pt checkpoint

evaluation metrics

plots

sample prediction images

annotated traffic video

README

concise explanation of methodology and results



27. Codex execution instructions

You are the coding agent implementing this specification.


Before writing substantial code:



Inspect the official YOLOv7 repository structure.

Determine the exact training command and configuration expected by that repository.

Do not invent incompatible command-line arguments.

Check current dependency compatibility with Google Colab.

Keep changes minimal and reproducible.


When a choice is ambiguous, prefer the simplest approach that satisfies this specification.


Do not ask for clarification for routine implementation details.


However, if a required external dataset cannot legally/technically be downloaded or does not contain the required vehicle classes, stop and report:


DATASET BLOCKER

Then identify exactly what is missing and suggest the smallest compatible replacement.


At completion, provide:



files created/modified

exact commands to run

dataset source and class mapping

training configuration

actual results

known limitations

next recommended step


Do not claim that training succeeded unless it actually ran successfully.

