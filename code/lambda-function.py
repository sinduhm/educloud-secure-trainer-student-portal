import json
import os
import uuid
import base64
import pymysql
import boto3
from urllib.parse import quote, unquote_plus

# ============================================================
# EDUCloud - FINAL LAMBDA
# ============================================================

RDS_HOST = "educloud-db.c76oao686q4m.eu-north-1.rds.amazonaws.com"
RDS_DATABASE = "educloud-db"
RDS_USER = "admin"
RDS_PASSWORD = "admin123"

S3_BUCKET = "educloud-materials-fr1"
CLOUDFRONT_DOMAIN = "---"
SNS_TOPIC_ARN = "arn:aws:sns:eu-north-1:757235735095:educloud:cba5851e-25e2-462b-bac1-ec7df0e87533"
REGION = "eu-north-1"

# ============================================================
# AWS CLIENTS
# ============================================================
s3 = boto3.client("s3", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

# ============================================================
# CORS
# ============================================================
CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers":
        "Content-Type,X-Amz-Date,Authorization,"
        "X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Methods": "POST,OPTIONS"
}

# ============================================================
# RESPONSE
# ============================================================
def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, default=str)
    }

# ============================================================
# DATABASE
# ============================================================
def get_connection():
    return pymysql.connect(
        host=RDS_HOST,
        user=RDS_USER,
        password=RDS_PASSWORD,
        database=RDS_DATABASE,
        port=3306,
        connect_timeout=10,
        read_timeout=15,
        write_timeout=15,
        cursorclass=pymysql.cursors.DictCursor
    )

# ============================================================
# REQUEST DATA
# ============================================================
def get_data(event):
    body = event.get("body")
    if body is None:
        return {}
    if isinstance(body, dict):
        return body
    if isinstance(body, str):
        if not body.strip():
            return {}
        # API Gateway sometimes sends base64 encoded body
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")
        return json.loads(body)
    return {}

# ============================================================
# HELPERS
# ============================================================
def clean(value):
    if value is None:
        return ""
    return str(value).strip()

def valid_zip(filename):
    filename = clean(filename).lower()
    return filename.endswith(".zip")

def valid_material_file(filename):
    # Trainer materials: accept any non-empty filename.
    return bool(clean(filename))

def safe_filename(filename):
    filename = os.path.basename(clean(filename))
    filename = filename.replace(" ", "_")
    return filename

# ============================================================
# SNS - SUBSCRIBE STUDENT EMAIL
# ============================================================
def subscribe_student_to_sns(email):
    email = clean(email).lower()
    if not email:
        return
    try:
        result = sns.subscribe(
            TopicArn=SNS_TOPIC_ARN,
            Protocol="email",
            Endpoint=email
        )
        print("SNS subscription created for:", email)
        print("Subscription ARN:", result.get("SubscriptionArn"))
    except Exception as error:
        print("SNS SUBSCRIBE ERROR:", email, str(error))

# ============================================================
# ADD STUDENT
# ============================================================
def add_student(name, email, group):
    name = clean(name)
    email = clean(email).lower()
    group = clean(group)

    if not name:
        return response(400, {"message": "Student name is required"})
    if not email:
        return response(400, {"message": "Student email is required"})
    if not group:
        return response(400, {"message": "Student group is required"})

    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM students WHERE email = %s",
                (email,)
            )
            existing = cursor.fetchone()
            if existing:
                return response(409, {
                    "message": "Student email already exists",
                    "student_id": existing["id"]
                })

            cursor.execute(
                """
                INSERT INTO students (name, email, `group`)
                VALUES (%s, %s, %s)
                """,
                (name, email, group)
            )
            student_id = cursor.lastrowid
        connection.commit()

        # ====================================================
        # SNS SUBSCRIPTION
        # ====================================================
        subscribe_student_to_sns(email)

        return response(200, {
            "message": "Student added successfully",
            "student_id": student_id,
            "sns": "Email subscription requested"
        })
    except Exception as error:
        if connection:
            connection.rollback()
        print("ADD STUDENT ERROR:", str(error))
        return response(500, {"message": "Unable to add student", "error": str(error)})
    finally:
        if connection:
            connection.close()

# ============================================================
# GET STUDENTS
# ============================================================
def get_students():
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, email, `group`
                FROM students
                ORDER BY id DESC
                """
            )
            rows = cursor.fetchall()
        return response(200, {"students": rows})
    except Exception as error:
        print("GET STUDENTS ERROR:", str(error))
        return response(500, {"message": "Unable to load students", "error": str(error)})
    finally:
        if connection:
            connection.close()

# ============================================================
# ADD TRAINER
# ============================================================
def add_trainer(name, email, subject):
    name = clean(name)
    email = clean(email).lower()
    subject = clean(subject)

    if not name:
        return response(400, {"message": "Trainer name is required"})
    if not email:
        return response(400, {"message": "Trainer email is required"})
    if not subject:
        return response(400, {"message": "Trainer subject is required"})

    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM trainers WHERE email = %s",
                (email,)
            )
            existing = cursor.fetchone()
            if existing:
                return response(409, {
                    "message": "Trainer email already exists",
                    "trainer_id": existing["id"]
                })

            cursor.execute(
                """
                INSERT INTO trainers (name, email, subject)
                VALUES (%s, %s, %s)
                """,
                (name, email, subject)
            )
            trainer_id = cursor.lastrowid
        connection.commit()
        return response(200, {
            "message": "Trainer added successfully",
            "trainer_id": trainer_id
        })
    except Exception as error:
        if connection:
            connection.rollback()
        print("ADD TRAINER ERROR:", str(error))
        return response(500, {"message": "Unable to add trainer", "error": str(error)})
    finally:
        if connection:
            connection.close()

# ============================================================
# GET TRAINERS
# ============================================================
def get_trainers():
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, email, subject
                FROM trainers
                ORDER BY id DESC
                """
            )
            rows = cursor.fetchall()
        return response(200, {"trainers": rows})
    except Exception as error:
        print("GET TRAINERS ERROR:", str(error))
        return response(500, {"message": "Unable to load trainers", "error": str(error)})
    finally:
        if connection:
            connection.close()

# ============================================================
# DASHBOARD STATISTICS
# ============================================================
def get_stats():
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM students")
            students = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM trainers")
            trainers = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM uploads")
            materials = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM submissions")
            submissions = cursor.fetchone()["total"]

        return response(200, {
            "students": students,
            "trainers": trainers,
            "materials": materials,
            "submissions": submissions
        })
    except Exception as error:
        print("STATS ERROR:", str(error))
        return response(500, {"message": "Unable to load statistics", "error": str(error)})
    finally:
        if connection:
            connection.close()

# ============================================================
# GET MATERIALS
#
# IMPORTANT:
# We return the ACTUAL s3_key stored in RDS.
# We do NOT reconstruct the key from filename.
# ============================================================
def get_materials():
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, filename, uploader, timestamp, s3_key
                FROM uploads
                WHERE s3_key IS NOT NULL AND s3_key <> ''
                ORDER BY timestamp DESC
                """
            )
            rows = cursor.fetchall()

        materials = []
        for row in rows:
            key = row["s3_key"]
            download_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": S3_BUCKET, "Key": key},
                ExpiresIn=3600
            )
            materials.append({
                "id": row["id"],
                "filename": row["filename"],
                "uploader": row["uploader"],
                "timestamp": row["timestamp"],
                "s3_key": key,
                "download_url": download_url
            })

        return response(200, {"materials": materials})
    except Exception as error:
        print("MATERIAL ERROR:", str(error))
        return response(500, {"message": "Unable to load materials", "error": str(error)})
    finally:
        if connection:
            connection.close()

# ============================================================
# GET MATERIAL DOWNLOAD URL
#
# CloudFront is used instead of direct S3 URL.
# ============================================================
def download_material(filename, s3_key=None):
    filename = clean(filename)
    s3_key = clean(s3_key)

    if not filename and not s3_key:
        return response(400, {"message": "filename or s3_key is required"})

    connection = None
    try:
        if not s3_key:
            connection = get_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT s3_key FROM uploads
                    WHERE filename = %s AND s3_key IS NOT NULL
                    ORDER BY id DESC LIMIT 1
                    """,
                    (filename,)
                )
                row = cursor.fetchone()
                if not row:
                    return response(404, {"message": "Material not found"})
                s3_key = row["s3_key"]

        download_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": s3_key},
            ExpiresIn=3600
        )
        return response(200, {"download_url": download_url, "s3_key": s3_key})
    except Exception as error:
        print("DOWNLOAD ERROR:", str(error))
        return response(500, {"message": "Unable to create download URL", "error": str(error)})
    finally:
        if connection:
            connection.close()

# ============================================================
# GENERATE TRAINER MATERIAL UPLOAD URL
# ============================================================
def get_upload_url(filename, content_type, uploader):
    filename = safe_filename(filename)
    uploader = clean(uploader)
    content_type = clean(content_type)

    if not filename:
        return response(400, {"message": "filename is required"})
    if not uploader:
        return response(400, {"message": "uploader is required"})
    if not valid_material_file(filename):
        return response(400, {"message": "A valid filename is required"})

    unique_id = str(uuid.uuid4()).replace("-", "")[:12]
    s3_key = "materials/" + unique_id + "_" + filename

    try:
        url = s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": S3_BUCKET, "Key": s3_key, "ContentType": content_type},
            ExpiresIn=900
        )
        return response(200, {"upload_url": url, "s3_key": s3_key, "filename": filename})
    except Exception as error:
        print("UPLOAD URL ERROR:", str(error))
        return response(500, {"message": "Unable to create upload URL", "error": str(error)})

# ============================================================
# RECORD TRAINER UPLOAD
# ============================================================
def record_upload(filename, uploader, s3_key):
    filename = safe_filename(filename)
    uploader = clean(uploader)
    s3_key = clean(s3_key)

    if not filename:
        return response(400, {"message": "filename is required"})
    if not uploader:
        return response(400, {"message": "uploader is required"})
    if not s3_key:
        return response(400, {"message": "s3_key is required"})
    if not valid_material_file(filename):
        return response(400, {"message": "A valid filename is required"})

    connection = None
    try:
        # Verify object actually exists in S3
        s3.head_object(Bucket=S3_BUCKET, Key=s3_key)

        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO uploads (filename, uploader, s3_key)
                VALUES (%s, %s, %s)
                """,
                (filename, uploader, s3_key)
            )
            upload_id = cursor.lastrowid
        connection.commit()

        return response(200, {
            "message": "Material uploaded successfully",
            "upload_id": upload_id,
            "s3_key": s3_key
        })
    except Exception as error:
        if connection:
            connection.rollback()
        print("RECORD UPLOAD ERROR:", str(error))
        return response(500, {"message": "Unable to record upload", "error": str(error)})
    finally:
        if connection:
            connection.close()

# ============================================================
# GENERATE ASSIGNMENT UPLOAD URL
# ============================================================
def get_assignment_upload_url(student_email, assignment_name, filename, content_type):
    student_email = clean(student_email).lower()
    assignment_name = clean(assignment_name)
    filename = safe_filename(filename)
    content_type = clean(content_type)

    if not student_email:
        return response(400, {"message": "Student email is required"})
    if not assignment_name:
        return response(400, {"message": "Assignment name is required"})
    if not filename:
        return response(400, {"message": "Assignment filename is required"})
    if not valid_zip(filename):
        return response(400, {"message": "Only .zip files are accepted"})

    email_part = student_email.replace("@", "_").replace(".", "_")
    assignment_part = assignment_name.replace("/", "_").replace("\\", "_").replace(" ", "_")
    unique_id = str(uuid.uuid4()).replace("-", "")[:12]

    s3_key = (
        "assignments/" + email_part + "/" + assignment_part + "/"
        + unique_id + "_" + filename
    )

    try:
        url = s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": S3_BUCKET, "Key": s3_key, "ContentType": content_type},
            ExpiresIn=900
        )
        return response(200, {"upload_url": url, "s3_key": s3_key, "filename": filename})
    except Exception as error:
        print("ASSIGNMENT URL ERROR:", str(error))
        return response(500, {"message": "Unable to create assignment upload URL", "error": str(error)})

# ============================================================
# SUBMIT ASSIGNMENT
# ============================================================
def submit_assignment(student_email, assignment_name, filename, s3_key):
    student_email = clean(student_email).lower()
    assignment_name = clean(assignment_name)
    filename = safe_filename(filename)
    s3_key = clean(s3_key)

    if not student_email:
        return response(400, {"message": "Student email is required"})
    if not assignment_name:
        return response(400, {"message": "Assignment name is required"})
    if not filename:
        return response(400, {"message": "Filename is required"})
    if not s3_key:
        return response(400, {"message": "S3 key is required"})
    if not valid_zip(filename):
        return response(400, {"message": "Only .zip files are accepted"})

    connection = None
    try:
        # Verify uploaded file exists
        s3.head_object(Bucket=S3_BUCKET, Key=s3_key)

        connection = get_connection()
        with connection.cursor() as cursor:
            # Verify student exists
            cursor.execute(
                "SELECT id FROM students WHERE email = %s",
                (student_email,)
            )
            student = cursor.fetchone()
            if not student:
                return response(404, {"message": "Student email is not registered"})

            cursor.execute(
                """
                INSERT INTO submissions (student_email, assignment_name, filename, s3_key)
                VALUES (%s, %s, %s, %s)
                """,
                (student_email, assignment_name, filename, s3_key)
            )
            submission_id = cursor.lastrowid
        connection.commit()

        # ====================================================
        # EXISTING ASSIGNMENT SNS
        # ====================================================
        try:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="EduCloud - New Assignment Submission",
                Message=json.dumps({
                    "message": "New assignment submitted",
                    "submission_id": submission_id,
                    "student_email": student_email,
                    "assignment_name": assignment_name,
                    "filename": filename,
                    "s3_key": s3_key
                }, indent=2)
            )
        except Exception as sns_error:
            print("ASSIGNMENT SNS ERROR:", str(sns_error))

        return response(200, {
            "message": "Assignment submitted successfully",
            "submission_id": submission_id,
            "s3_key": s3_key
        })
    except Exception as error:
        if connection:
            connection.rollback()
        print("SUBMISSION ERROR:", str(error))
        return response(500, {"message": "Unable to submit assignment", "error": str(error)})
    finally:
        if connection:
            connection.close()

# ============================================================
# GET SUBMISSIONS
# ============================================================
def get_submissions():
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, student_email, assignment_name, filename, s3_key, timestamp
                FROM submissions
                ORDER BY timestamp DESC
                LIMIT 100
                """
            )
            rows = cursor.fetchall()

        submissions = []
        for row in rows:
            download_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": S3_BUCKET, "Key": row["s3_key"]},
                ExpiresIn=3600
            )
            submissions.append({
                "id": row["id"],
                "student_email": row["student_email"],
                "assignment_name": row["assignment_name"],
                "filename": row["filename"],
                "s3_key": row["s3_key"],
                "timestamp": row["timestamp"],
                "download_url": download_url
            })

        return response(200, {"submissions": submissions})
    except Exception as error:
        print("SUBMISSIONS ERROR:", str(error))
        return response(500, {"message": "Unable to load submissions", "error": str(error)})
    finally:
        if connection:
            connection.close()

# ============================================================
# S3 MATERIAL UPLOAD -> SNS
# ============================================================
def handle_s3_material_upload(event):
    print("========== S3 MATERIAL UPLOAD ==========")
    connection = None
    try:
        records = event.get("Records", [])
        if not records:
            print("No S3 records found.")
            return {"statusCode": 200, "message": "No S3 records found"}

        for record in records:
            event_name = record.get("eventName", "")
            # Only process ObjectCreated events
            if not event_name.startswith("ObjectCreated:"):
                print("Ignoring S3 event:", event_name)
                continue

            event_source = record.get("eventSource")
            if event_source != "aws:s3":
                print("Ignoring non-S3 event.")
                continue

            s3_data = record.get("s3", {})
            bucket_name = s3_data.get("bucket", {}).get("name", "")
            object_data = s3_data.get("object", {})
            object_key = object_data.get("key", "")
            # S3 object key is URL encoded
            object_key = unquote_plus(object_key)

            print("Bucket:", bucket_name)
            print("Object:", object_key)

            # Make sure event belongs to our bucket
            if bucket_name != S3_BUCKET:
                print("Ignoring different bucket.")
                continue

            # =================================================
            # ONLY MATERIALS
            # =================================================
            if not object_key.startswith("materials/"):
                print("Ignoring non-material object:", object_key)
                continue

            filename = os.path.basename(object_key)
            print("New material:", filename)

            # =================================================
            # GET ALL STUDENTS FROM RDS
            # =================================================
            connection = get_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, name, email FROM students
                    WHERE email IS NOT NULL AND email <> ''
                    ORDER BY id
                    """
                )
                students = cursor.fetchall()

            print("Students found:", len(students))
            if not students:
                print("No students registered.")
                continue

            # =================================================
            # SNS MESSAGE
            # =================================================
            message = (
                "Hello EduCloud Student,\n\n"
                "A new learning material has been uploaded by a trainer.\n\n"
                "File: " + filename + "\n\n"
                "S3 Key: " + object_key + "\n\n"
                "Please log in to the EduCloud portal to access the new material.\n\n"
                "EduCloud Learning Platform"
            )

            # =================================================
            # PUBLISH TO SNS
            # =================================================
            sns_response = sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="EduCloud - New Learning Material",
                Message=message
            )
            print("SNS notification sent successfully.")
            print("SNS Message ID:", sns_response.get("MessageId"))

            if connection:
                connection.close()
                connection = None

        return {"statusCode": 200, "message": "Material SNS notification processed"}
    except Exception as error:
        if connection:
            connection.close()
        print("S3 MATERIAL SNS ERROR:", str(error))
        raise

# ============================================================
# MAIN HANDLER
# ============================================================
def lambda_handler(event, context):
    print("========== EDUCloud Lambda ==========")
    print(json.dumps(event, default=str))

    # ========================================================
    # S3 EVENT
    # ========================================================
    # S3 sends an event containing Records.
    # API Gateway requests do not normally contain an S3 eventSource.
    if event.get("Records"):
        first_record = event["Records"][0]
        if first_record.get("eventSource") == "aws:s3":
            return handle_s3_material_upload(event)

    # ========================================================
    # HTTP METHOD
    # ========================================================
    method = event.get("httpMethod")
    if not method:
        method = event.get("requestContext", {}).get("http", {}).get("method")

    # ========================================================
    # CORS
    # ========================================================
    if method == "OPTIONS":
        return response(200, {"message": "CORS OK"})

    # ========================================================
    # GET BODY
    # ========================================================
    try:
        data = get_data(event)
    except Exception as error:
        return response(400, {"message": "Invalid JSON", "error": str(error)})

    action = clean(data.get("action"))
    print("ACTION:", action)

    # ========================================================
    # STUDENTS
    # ========================================================
    if action == "addStudent":
        return add_student(data.get("name"), data.get("email"), data.get("group"))
    if action == "getStudents":
        return get_students()

    # ========================================================
    # TRAINERS
    # ========================================================
    if action == "addTrainer":
        return add_trainer(data.get("name"), data.get("email"), data.get("subject"))
    if action == "getTrainers":
        return get_trainers()

    # ========================================================
    # DASHBOARD
    # ========================================================
    if action == "getStats":
        return get_stats()

    # ========================================================
    # MATERIALS
    # ========================================================
    if action == "getMaterials":
        return get_materials()
    if action == "downloadMaterial":
        return download_material(data.get("filename"), data.get("s3_key"))

    # ========================================================
    # TRAINER MATERIAL UPLOAD
    # ========================================================
    if action == "getUploadUrl":
        return get_upload_url(
            data.get("filename"),
            data.get("content_type", "application/octet-stream"),
            data.get("uploader")
        )
    if action == "recordUpload":
        return record_upload(data.get("filename"), data.get("uploader"), data.get("s3_key"))

    # ========================================================
    # STUDENT ASSIGNMENT
    # ========================================================
    if action == "getAssignmentUploadUrl":
        return get_assignment_upload_url(
            data.get("student_email"),
            data.get("assignment_name"),
            data.get("filename"),
            data.get("content_type", "application/zip")
        )
    if action == "submitAssignment":
        return submit_assignment(
            data.get("student_email"),
            data.get("assignment_name"),
            data.get("filename"),
            data.get("s3_key")
        )
    if action == "getSubmissions":
        return get_submissions()

    # ========================================================
    # UNKNOWN ACTION
    # ========================================================
    return response(400, {"message": "Unknown action", "action": action})
