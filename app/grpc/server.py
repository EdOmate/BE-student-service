import grpc
from grpc import aio

from app.grpc.generated import student_pb2_grpc
from app.grpc.services import StudentService


async def start_grpc_server():
    server = aio.server()

    student_pb2_grpc.add_StudentServiceServicer_to_server(
        StudentService(),
        server,
    )

    server.add_insecure_port("[::]:50051")

    await server.start()

    print("✅ gRPC Server started on :50051")

    return server