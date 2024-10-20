import cv2
import grpc
import image_stream_pb2
import image_stream_pb2_grpc
import time
import sys
import ssl

def main():
    # Replace with your Cloud Run service URL
    SERVICE_URL = "https://spot-microservice-856883549533.us-central1.run.app"  # e.g., "spot-microservice-abc123.run.app"

    # Establish a secure channel (gRPC over HTTPS)
    # Cloud Run uses SSL certificates, so we need to create SSL credentials
    try:
        # Load default SSL credentials
        credentials = grpc.ssl_channel_credentials()
        channel = grpc.secure_channel(f"{SERVICE_URL}:443", credentials)
        stub = image_stream_pb2_grpc.ImageStreamStub(channel)
    except Exception as e:
        print(f"Failed to create gRPC channel: {e}")
        sys.exit(1)

    # Initialize OpenCV video capture (0 is usually the default camera)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open video capture.")
        sys.exit(1)

    print("Starting video capture and sending images to the microservice...")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame.")
                break

            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Failed to encode frame.")
                continue

            image_bytes = buffer.tobytes()

            # Create ImageRequest
            request = image_stream_pb2.ImageRequest(image_data=image_bytes)

            # Send the image via gRPC
            try:
                response = stub.SendImage(request)
                print(f"Server Response: {response.message}")
            except grpc.RpcError as rpc_error:
                print(f"gRPC Error: {rpc_error.code()} - {rpc_error.details()}")

            # Display the captured frame (optional)
            cv2.imshow('Sending to Microservice', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Quitting...")
                break

            # Control frame rate (e.g., 10 FPS)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Interrupted by user.")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Released video capture and destroyed all windows.")

if __name__ == "__main__":
    main()
