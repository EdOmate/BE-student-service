from app.grpc.generated import student_pb2
from app.grpc.generated import student_pb2_grpc


class StudentService(student_pb2_grpc.StudentServiceServicer):

    async def GetStudent(self, request, context):

        return student_pb2.StudentResponse(
            id=request.student_id,
            first_name="Somesh",
            last_name="Verma",
            email="somesh@test.com",
        )
