from app.services.face_recognition_service import _blocking_represent_one_image
extracted_faces = _blocking_represent_one_image("storage/events/11/778fb0ca-40da-4cbd-9ba2-ee6a9a7d022f.JPG")
# from deepface import DeepFace
# extracted_faces = DeepFace.represent(
    # img_path="storage/events/11/778fb0ca-40da-4cbd-9ba2-ee6a9a7d022f.JPG",
    # model_name="Dlib"
# )

print(extracted_faces)




