from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials, firestore
from payos import PayOS, PaymentData, ItemData
import os
import pytz
import pytz
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from datetime import date, datetime, time, timedelta
from google.api_core.datetime_helpers import DatetimeWithNanoseconds

# Tải các biến môi trường từ file .env
load_dotenv()

# Lấy thông tin từ biến môi trường
PAYOS_API_KEY = os.getenv("PAYOS_API_KEY")
PAYOS_CLIENT_ID = os.getenv("PAYOS_CLIENT_ID")
PAYOS_CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY")
API_URL = os.getenv("API_URL")

# Khởi tạo ứng dụng FastAPI
app = FastAPI()

if not firebase_admin._apps:
    cred = credentials.Certificate(r"D:\subject\ie402\cinema-ticket-react-native\MovieBookingAppBackend\cinema-76c5b-firebase-adminsdk-yi33h-ffc955554b.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Cấu hình PayOS Client
payos = PayOS(
    api_key=PAYOS_API_KEY,  # API key
    client_id=PAYOS_CLIENT_ID,  # Client ID từ PayOS
    checksum_key=PAYOS_CHECKSUM_KEY  # Checksum Key từ PayOS
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn (hoặc có thể chỉ định các nguồn cụ thể như: ['http://localhost:8081'])
    allow_credentials=True,  # Cho phép sử dụng cookie
    allow_methods=["*"],  # Cho phép tất cả các phương thức HTTP (GET, POST, PUT, DELETE, ...)
    allow_headers=["*"],  # Cho phép tất cả các tiêu đề
)

class Seat(BaseModel):
  seat: str = ""
  available: bool = True
  type: str = ""

class Showtime(BaseModel):
  start_time: datetime = "1999-03-30T17:00:00.610000Z"
  end_time: datetime = "1999-03-30T17:00:00.610000Z"
  cinema_name: str = ""
  location: str = ""
  hall_name: str = ""
  seats: list[Seat] = Field(..., example=[{"seat": "A1", "available": True, "type": "vip"}])

class Movie(BaseModel):
  title: str = ""
  description: str = ""
  posterUrl: str = ""
  trailerUrl: str = ""
  duration: int = 1
  genres: List[str] = None
  imdbRating: Optional[float] = 1.5
  rottenTomatoesRating: Optional[int] = 1
  releaseDate: datetime = "1999-03-30T17:00:00.610000Z"
  showtimes: Optional[Dict] = []

class Ticket(BaseModel):
  user_id: str = ""
  movie_id: str = ""
  movie_title: str = ""
  cinema_name: str = ""
  hall_name: str = ""
  showtime: datetime = "1999-03-30T17:00:00.610000Z"
  seat_number: str = ""
  status: int = 1
  price: int = 1
  created_at: datetime = "1999-03-30T17:00:00.610000Z"
  updated_at: datetime = "1999-03-30T17:00:00.610000Z"
  cancel_reason: str = ""

class User(BaseModel):
  name: str = ""
  email: str = ""
  password: str = ""
  dob: datetime = "1999-03-30T17:00:00.610000Z"
  gender: int = 1
  phone_number: str = ""
  is_admin: bool = False
  created_at: datetime = "2024-11-30T17:00:00.610000Z"
  point: int = 1

# Model cho booking response
class BookingResponse(BaseModel):
    ticket_ids: List[str]

# Model thanh toán
class PaymentRequest(BaseModel):
    order_id: int
    amount: int
    description: str
    movie_id: str  # ID của bộ phim
    showtime: datetime  # Thời gian chiếu
    selectedSeats: List[str]  # Danh sách ghế đã chọn
  
class Hall(BaseModel):
  name: str = Field(..., example="Room A")
  seat_capacity: int = Field(..., example=100)

class Cinema(BaseModel):
  name: str = Field(..., example="Cinema 1")
  location: str = Field(..., example="123 Main Street")
  halls: list[Hall] = Field(..., example=[{"name": "Hall A", "seat_capacity": 100}])

# Mock admin authentication function
def get_current_admin_user():
  # Giả định là đã đăng nhập và xác thực, trả về user là admin
  return True  # Thay bằng logic xác thực thực tế

@app.get("/check-firebase")
async def check_firebase_connection():
    try:
        # Kiểm tra kết nối Firestore bằng cách lấy tất cả tài liệu trong collection 'movies'
        test_ref = db.collection("movies")
        docs = test_ref.stream()

        movie_list = []
        for doc in docs:
            movie_data = doc.to_dict()  # Lấy dữ liệu từ tài liệu
            movie_data["id"] = doc.id  # Thêm ID tài liệu
            movie_list.append(movie_data)

        print("Kết nối thành công! Dữ liệu lấy được từ Firestore:")
        print(movie_list)

        return {"message": "Kết nối thành công!", "data": movie_list}
    except Exception as e:
        print("Kết nối thất bại! Lỗi:", str(e))
        return {"message": "Kết nối thất bại!", "error": str(e)}

# # 1. Lấy danh sách phim
@app.get("/movies", response_model=List[Dict])
async def get_movies():
  print("Fetching movies from Firestore...")
  """
  API để lấy danh sách phim cùng với ID.
  """
  movies_ref = db.collection('movies')
  movies = movies_ref.stream()
  movie_list = []

  for movie in movies:
      movie_data = movie.to_dict()  # Dữ liệu của phim
      movie_data["id"] = movie.id  # Lấy ID của tài liệu
      movie_list.append(movie_data)
      print({"message123331": "Kết nối thành công!", "data": movie_data})
  return movie_list


@app.get("/movies/all", response_model=List[Movie])
async def get_all_movies():
    movies_ref = db.collection("movies").stream()
    all_movies = []

    for movie_doc in movies_ref:
        movie_data = movie_doc.to_dict()
        movie_data["id"] = movie_doc.id  # Add movie ID to the response

        # Fetch showtimes subcollection
        showtimes_ref = db.collection("movies").document(movie_doc.id).collection("showtimes").stream()
        showtimes = [showtime_doc.to_dict() for showtime_doc in showtimes_ref]

        # Attach showtimes to the movie data
        movie_data["showtimes"] = showtimes
        all_movies.append(movie_data)
   
    return all_movies

from datetime import timezone

@app.get("/movies/upcoming", response_model=List[Dict])
async def get_upcoming_movies():
    """
    API trả về danh sách phim chỉ với showtimes có start_time > thời gian hiện tại (GMT+7).
    Tất cả thời gian start_time được chuyển sang múi giờ GMT+7.
    """
    try:
        current_time = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(hours=7)  # Lấy thời gian hiện tại (GMT+7)
        movies_ref = db.collection("movies").stream()
        upcoming_movies = []

        for movie_doc in movies_ref:
            movie_data = movie_doc.to_dict()
            movie_data["id"] = movie_doc.id  # Thêm movie ID vào dữ liệu
            filtered_showtimes = []

            # Lấy subcollection `showtimes`
            showtimes_ref = db.collection("movies").document(movie_doc.id).collection("showtimes").stream()
            for showtime_doc in showtimes_ref:
                showtime_data = showtime_doc.to_dict()

                # Chuyển `start_time` sang offset-aware và GMT+7
                start_time = datetime.fromisoformat(showtime_data["start_time"].replace("Z", "+00:00")).astimezone(timezone.utc) + timedelta(hours=7)
                showtime_data["start_time"] = start_time.isoformat()

                # Chuyển `end_time` sang offset-aware và GMT+7
                end_time = datetime.fromisoformat(showtime_data["end_time"].replace("Z", "+00:00")).astimezone(timezone.utc) + timedelta(hours=7)
                showtime_data["end_time"] = end_time.isoformat()

                # Kiểm tra nếu `start_time` > `current_time`
                if start_time > current_time:
                    filtered_showtimes.append(showtime_data)

            if filtered_showtimes:
                # movie_data["showtimes"] = filtered_showtimes
                upcoming_movies.append(movie_data)

        return upcoming_movies

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 2. Lấy thông tin chi tiết của một phim
@app.get("/movies/{movie_id}", response_model=Movie)
async def get_movie(movie_id: str):
    # Truy vấn tài liệu movie từ Firestore
    movie_ref = db.collection("movies").document(movie_id)
    movie_doc = movie_ref.get()

    if not movie_doc.exists:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Chuyển đổi dữ liệu movie
    movie_data = movie_doc.to_dict()

    # Lấy sub-collection showtimes và chuyển đổi thành dict
    showtimes_ref = movie_ref.collection("showtimes")
    showtimes_docs = showtimes_ref.stream()

    # Tạo dictionary cho showtimes
    showtimes_dict = {}
    for doc in showtimes_docs:
        showtime_data = doc.to_dict()
        showtimes_dict[doc.id] = showtime_data

    # Thêm showtimes vào movie_data
    movie_data["showtimes"] = showtimes_dict

    return Movie(**movie_data)

@app.post("/movies/")
async def add_movie(movie: Movie, admin: bool = Depends(get_current_admin_user)):
  if not admin:
      raise HTTPException(status_code=403, detail="Not authorized")
  movie_ref = db.collection('movies').document()
  movie_ref.set(movie.dict())
  return movie_ref.id

# 4. Cập nhật thông tin phim (chỉ admin)
@app.put("/movies/{movie_id}", response_model=str)
async def update_movie(movie_id: str, movie: Movie, admin: bool = Depends(get_current_admin_user)):
  if not admin:
      raise HTTPException(status_code=403, detail="Not authorized")
  movie_ref = db.collection('movies').document(movie_id)
  if not movie_ref.get().exists:
      raise HTTPException(status_code=404, detail="Movie not found")
  movie_ref.update(movie.dict())
  return movie_id

# 5. Xóa phim (chỉ admin)
@app.delete("/movies/{movie_id}", response_model=str)
async def delete_movie(movie_id: str, admin: bool = Depends(get_current_admin_user)):
  if not admin:
      raise HTTPException(status_code=403, detail="Not authorized")
  movie_ref = db.collection('movies').document(movie_id)
  if not movie_ref.get().exists:
      raise HTTPException(status_code=404, detail="Movie not found")
  showtime_ref = movie_ref.collection('showtimes')
  showtimes = showtime_ref.stream()
  for showtime in showtimes:
      # Xóa từng document trong subcollection 'showtimes'
      showtime_ref.document(showtime.id).delete()
  movie_ref.delete()
  return movie_id

#Get tickets
@app.get("/tickets", response_model=List[Dict])
async def get_tickets():
  tickets_ref = db.collection('tickets')
  tickets = tickets_ref.stream()
  ticket_list = []

  for ticket in tickets:
    ticket_data = ticket.to_dict()
    ticket_data["id"] = ticket.id
    ticket_list.append(ticket_data)

  return ticket_list

#Get users
@app.get("/users", response_model=List[Dict])
async def get_users():
  users_ref = db.collection('users').get()
  user_list = []

  for user in users_ref:
      user_data = user.to_dict()
      user_data["id"] = user.id  
      user_list.append(user_data)

  return user_list

#Get cinemas
@app.get("/cinemas", response_model=List[Dict])
async def get_cinema():
  cinemas_ref = db.collection('cinemas')
  cinemas = cinemas_ref.stream()
  cinema_list = []

  for cinema in cinemas:
      halls_ref = db.collection('cinemas/' + cinema.id + '/halls')
      halls = halls_ref.stream()
      hall_list = []
      for hall in halls:
          hall_data = hall.to_dict()
          hall_data["id"] = hall.id
          hall_list.append(hall_data)
          
      cinema_data = cinema.to_dict()
      cinema_data["halls"] = hall_list
      
      cinema_data["id"] = cinema.id
      cinema_list.append(cinema_data)

  return cinema_list

@app.post("/cinemas/")
async def add_cinema(cinema: Cinema, admin: bool = Depends(get_current_admin_user)):
  if not admin:
      raise HTTPException(status_code=403, detail="Not authorized")
  cinema_ref = db.collection('cinemas').document()
  cinema_data = {
      "name": cinema.name,
      "location": cinema.location,
  }
  cinema_ref.set(cinema_data)
  batch = db.batch()
  for hall in cinema.halls:
      hall_ref = cinema_ref.collection("halls").document()
      batch.set(hall_ref, hall.dict())

  # Commit the batch operation
  batch.commit()
  return cinema_ref.id

@app.put("/cinemas/{cinema_id}", response_model=str)
async def update_cinema(cinema_id: str, update_data: dict, admin: bool = Depends(get_current_admin_user)):
  if not admin:
      raise HTTPException(status_code=403, detail="Not authorized")

  cinema_ref = db.collection('cinemas').document(cinema_id)

  # Kiểm tra xem cinema có tồn tại không
  if not cinema_ref.get().exists:
      raise HTTPException(status_code=404, detail="Cinema not found")

  # Cập nhật thông tin của document chính 'cinema'
  cinema_update_fields = {key: value for key, value in update_data.items() if key != "halls"}
  if cinema_update_fields:
      cinema_ref.update(cinema_update_fields)

  # Xử lý các 'halls' trong subcollection
  halls_data = update_data.get("halls", [])
  halls_ref = cinema_ref.collection("halls")

  # Lấy danh sách các phòng chiếu hiện tại
  existing_halls = {hall.id: hall.to_dict() for hall in halls_ref.stream()}

  # Danh sách ID của các phòng chiếu cần giữ lại
  hall_ids_to_keep = set()

  for hall in halls_data:
      hall_id = hall.get("id")  # Sử dụng ID để nhận dạng
      hall_name = hall.get("name")
      seat_capacity = hall.get("seat_capacity")

      if not hall_name or seat_capacity is None:
          raise HTTPException(status_code=400, detail="Invalid hall data")

      if hall_id and hall_id in existing_halls:
          # Nếu ID tồn tại, cập nhật phòng chiếu
          halls_ref.document(hall_id).update({"name": hall_name, "seat_capacity": seat_capacity})
      else:
          # Nếu không có ID, tạo mới phòng chiếu
          new_hall_ref = halls_ref.document()
          new_hall_ref.set({"name": hall_name, "seat_capacity": seat_capacity})
          hall_id = new_hall_ref.id  # Lấy ID mới sau khi tạo

      hall_ids_to_keep.add(hall_id)

  # Xóa các phòng chiếu không nằm trong danh sách cập nhật
  for hall_id in existing_halls.keys():
      if hall_id not in hall_ids_to_keep:
          halls_ref.document(hall_id).delete()

  return cinema_id


@app.delete("/cinemas/{cinema_id}", response_model=str)
async def delete_cinema(cinema_id: str, admin: bool = Depends(get_current_admin_user)):
  if not admin:
      raise HTTPException(status_code=403, detail="Not authorized")
  cinema_ref = db.collection('cinemas').document(cinema_id)
  if not cinema_ref.get().exists:
      raise HTTPException(status_code=404, detail="Cinema not found")
  halls_ref = cinema_ref.collection('halls')

  # Lấy danh sách tất cả các hall trong subcollection
  halls = halls_ref.stream()
  for hall in halls:
      # Xóa từng document trong subcollection 'halls'
      halls_ref.document(hall.id).delete()
  cinema_ref.delete()
  return cinema_id

@app.get("/movies/{movie_id}/showtimes", response_model=List[Dict])
async def get_showtimes(movie_id: str):
  showtimes_ref = db.collection('movies').document(movie_id).collection('showtimes')
  showtimes = showtimes_ref.stream()
  showtime_list = []

  for showtime in showtimes:
      showtime_data = showtime.to_dict()
      
      showtime_data["id"] = showtime.id
      showtime_list.append(showtime_data)

  return showtime_list

@app.post("/movies/{movie_id}/showtimes")
async def add_showtime(movie_id: str, showtime_data: dict, admin: bool = Depends(get_current_admin_user)):
  if not admin:
    raise HTTPException(status_code=403, detail="Not authorized")
  showtime_ref = db.collection('movies').document(movie_id).collection('showtimes')

  new_showtime_ref = showtime_ref.document()  # Tạo ID tự động
  new_showtime_ref.set(showtime_data)
  return new_showtime_ref.id

@app.put("/movies/{movie_id}/showtimes/{showtime_id}", response_model=str)
async def update_showtime(movie_id: str, showtime_id: str, update_data: dict, admin: bool = Depends(get_current_admin_user)):
  if not admin:
    raise HTTPException(status_code=403, detail="Not authorized")

  showtime_ref = db.collection('movies').document(movie_id).collection('showtimes').document(showtime_id)

  if not showtime_ref.get().exists:
      raise HTTPException(status_code=404, detail="Showtime not found")

  showtime_ref.update(update_data)

  return showtime_id

@app.delete("/movies/{movie_id}/showtimes/{showtime_id}", response_model=str)
async def delete_cinema(movie_id: str, showtime_id: str, admin: bool = Depends(get_current_admin_user)):
  if not admin:
      raise HTTPException(status_code=403, detail="Not authorized")
  showtime_ref = db.collection('movies').document(movie_id).collection('showtimes').document(showtime_id)
  if not showtime_ref.get().exists:
      raise HTTPException(status_code=404, detail="Showtime not found")
  showtime_ref.delete()
  return showtime_id

def normalize_to_datetime(value):
    if isinstance(value, str):
        # Xử lý chuỗi ISO 8601
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    elif isinstance(value, DatetimeWithNanoseconds):
        # Xử lý Firestore DatetimeWithNanoseconds
        return datetime.fromisoformat(value.isoformat())
    elif isinstance(value, datetime):
        # Đã là datetime
        return value
    else:
        raise ValueError(f"Không thể chuyển đổi giá trị: {value}")

# Set cứng giá ghế
SEAT_PRICES = {
    "vip": 150000,
    "normal": 100000
}

# 6. Đặt vé
@app.post("/bookings/", response_model=BookingResponse)
async def book_ticket(booking_data: dict):
    try:
        # 1. Tìm phim trong collection movies theo movie_id
        movie_ref = db.collection('movies').document(booking_data['movie_id'])
        movie = movie_ref.get()

        if not movie.exists:
            raise HTTPException(status_code=404, detail="Movie not found")

        movie_data = movie.to_dict()
        
        # 2. Truy vấn showtimes từ sub-collection của movie
        showtimes_ref = movie_ref.collection('showtimes')
        showtimes = showtimes_ref.stream()

        # 3. Kiểm tra xem showtime trong booking có trùng với thời gian bắt đầu của showtimes trong movie không
        showtime_match = None
        for doc in showtimes:
            showtime_data = doc.to_dict()
            if normalize_to_datetime(showtime_data['start_time']) == normalize_to_datetime(booking_data['showtime']):
                showtime_match = {**showtime_data, "id": doc.id}
                break

        if not showtime_match:
            raise HTTPException(status_code=404, detail="Showtime not found")

        # 4. Kiểm tra và cập nhật trạng thái ghế
        seats_dict = {seat['seat']: seat for seat in showtime_match['seats']}
        tickets_created = []  # Danh sách chứa các vé đã được tạo
        total_price = 0  # Tổng giá vé

        seats = booking_data.pop('seats')
        totalPrice = booking_data.pop('total_price')

        # Duyệt qua các ghế đã chọn và kiểm tra tính khả dụng
        for seat_code in seats:
            seat = seats_dict.get(seat_code)

            # Lấy giá của ghế và cộng vào tổng giá vé
            seat_price = SEAT_PRICES.get(seat['type'], 100000)  # Giá mặc định là 100000 nếu không tìm thấy loại ghế
            total_price += seat_price

            # Tạo vé cho ghế này (Chỉ lưu seat_number thay vì seats)
            created_at = datetime.now() - timedelta(hours=7)
            ticket_data = booking_data
            ticket_data['seat_number'] = seat_code  # Lưu ghế đã đặt
            ticket_data['status'] = 1  # Trạng thái "Đã đặt"
            ticket_data['price'] = SEAT_PRICES[seats_dict[seat_code]['type']]
            ticket_data['created_at'] = created_at
            ticket_data['updated_at'] = created_at

            # Không lưu trường 'seats' vào Firestore
            ticket_ref = db.collection('tickets').document()
            ticket_ref.set(ticket_data)

            tickets_created.append(ticket_ref.id)  # Thêm ID vé vào danh sách đã tạo

        # 5. Cập nhật lại thông tin ghế trong Firestore sau khi booking
        showtimes_ref.document(showtime_match["id"]).update({"seats": list(seats_dict.values())})

        return BookingResponse(
            ticket_ids=tickets_created,  # Trả về danh sách ID các vé đã tạo
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 7. Xem danh sách vé đã đặt của khách hàng
@app.get("/bookings/{user_id}", response_model=List[Ticket])
async def get_user_bookings(user_id: str):
    bookings_ref = db.collection('users').where('user_id', '==', user_id)
    bookings = bookings_ref.stream()
    booking_list = []
    for booking in bookings:
        booking_list.append(booking.to_dict())
    return booking_list

# 8. Tạo liên kết thanh toán
@app.post("/payment")
async def create_payment_link(payment_request: PaymentRequest):
    try:
        movie_ref = db.collection('movies').document(payment_request.movie_id)
        movie = movie_ref.get()

        if not movie.exists:
            raise HTTPException(status_code=404, detail="Movie not found")

        # Truy vấn showtimes từ sub-collection
        showtimes_ref = movie_ref.collection('showtimes')
        showtimes = showtimes_ref.stream()

        # Tìm showtime khớp với thời gian đặt vé
        showtime_match = None
        for doc in showtimes:
            showtime_data = doc.to_dict()
            if normalize_to_datetime(showtime_data['start_time']) == payment_request.showtime:
                showtime_match = {**showtime_data, "id": doc.id}
                break

        if not showtime_match:
            raise HTTPException(status_code=404, detail="Showtime not found")

        # Kiểm tra trạng thái ghế
        seats_dict = {seat['seat']: seat for seat in showtime_match['seats']}
        unavailable_seats = []

        for seat_code in payment_request.selectedSeats:
            seat = seats_dict.get(seat_code)
            if seat and not seat['available']:
                unavailable_seats.append(seat_code)
            elif seat:
                seat['available'] = False  # Đánh dấu ghế đã được đặt

        if unavailable_seats:
            raise HTTPException(status_code=400, detail=f"Seats {', '.join(unavailable_seats)} are not available")

        # Cập nhật trạng thái ghế trong Firestore
        # Đảm bảo các thay đổi ghế được lưu lại
        showtimes_ref.document(showtime_match["id"]).update({"seats": list(seats_dict.values())})

        # Tạo liên kết thanh toán
        payment_data = PaymentData(
            orderCode=payment_request.order_id,
            amount= 2000, #payment_request.amount,
            description=payment_request.description,
            cancelUrl=f"{API_URL}/cancel",
            returnUrl=f"{API_URL}/success"
        )
        payos_payment = payos.createPaymentLink(payment_data)
        return {"checkoutUrl": payos_payment.checkoutUrl}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Đặt lại trạng thái ghế nếu tạo vé không thành công và hủy thanh toán
@app.post("/release_seats")
async def release_seats(seats_data: dict):
    try:
        # Lấy thông tin phim từ Firestore
        movie_ref = db.collection('movies').document(seats_data['movie_id'])
        movie = movie_ref.get()

        if not movie.exists:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        movie_data = movie.to_dict()

        # Truy cập sub-collection 'showtimes' thay vì trực tiếp trong 'showtimes' field
        showtimes_ref = movie_ref.collection('showtimes')
        showtime_query = showtimes_ref.where('start_time', '==', seats_data['showtime']).limit(1)
        showtime_result = showtime_query.stream()

        showtime = None
        for doc in showtime_result:
            showtime = doc.to_dict()
            showtime_key = doc.id  # ID của showtime document

        if not showtime:
            raise HTTPException(status_code=404, detail="Showtime not found")

        # Kiểm tra và cập nhật ghế đã chọn
        seats_dict = {seat['seat']: seat for seat in showtime['seats']}

        # Duyệt qua các ghế cần mở lại và thay đổi trạng thái thành available: true
        for seat_code in seats_data['selectedSeats']:
            seat = seats_dict.get(seat_code)
            if seat and not seat['available']:
                seat['available'] = True  # Đặt lại trạng thái ghế thành có thể đặt

        # Cập nhật lại thông tin ghế trong sub-collection showtimes
        showtimes_ref.document(showtime_key).update({
            'seats': list(seats_dict.values())
        })

        return {"message": "Seats released successfully", "released_seats": seats_data['selectedSeats']}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 9. Kết quả thanh toán 
@app.get("/success")
async def success_page():
    return HTMLResponse(content="<h1>Thanh toán thành công</h1>", status_code=200)

@app.get("/cancel")
async def cancel_page():
    return HTMLResponse(content="<h1>Thanh toán đã bị hủy</h1>", status_code=200)

@app.get("/favicon.ico")
async def favicon():
    return HTMLResponse(content="", status_code=200)


# 10. API Tạo Người Dùng
@app.post("/users", response_model=str)
async def create_user(user: User):
    """
    Tạo người dùng mới sau khi kiểm tra email không trùng lặp.
    """
    # Kiểm tra email đã tồn tại
    users_ref = db.collection('users')
    user_query = users_ref.where('email', '==', user.email).stream()

    if any(user_query):  # Nếu email đã tồn tại
        raise HTTPException(status_code=400, detail="Email đã được sử dụng!")

    # Nếu email chưa tồn tại, tạo người dùng mới
    user_ref = db.collection('users').document()
    user_ref.set(user.dict())
    return user_ref.id

# 11. API Xem Chi Tiết Người Dùng
@app.get("/users/{user_id}", response_model=Dict)
async def get_user(user_id: str):
    user_ref = db.collection('users').document(user_id)
    user = user_ref.get()
    if not user.exists:
        raise HTTPException(status_code=404, detail="User not found")

    return user.to_dict()

# 12. API Xem Vé Của Người Dùng

@app.get("/tickets/{user_id}", response_model=List[Dict])
async def get_user_tickets(user_id: str):
    """
    API để xem thông tin các vé của người dùng.
    Lấy dữ liệu từ collection `tickets` và trả về danh sách vé.
    """
    # Lấy tất cả vé của user từ Firestore
    tickets_ref = db.collection('tickets').where('user_id', '==', user_id).stream()

    tickets = []
    for ticket in tickets_ref:
        ticket_data = ticket.to_dict()

        # Đảm bảo các trường cần thiết tồn tại trong dữ liệu và bổ sung ID
        ticket = {
            "id": ticket.id,  # Bổ sung ID của tài liệu
            "user_id": ticket_data.get("user_id", ""),
            "movie_title": ticket_data.get("movie_title", ""),
            "cinema_name": ticket_data.get("cinema_name", ""),
            "showtime": ticket_data.get("showtime", ""),
            "seat_number": ticket_data.get("seat_number", ""),
            "status": ticket_data.get("status", 0),
            "price": ticket_data.get("price", 0),
            "created_at": ticket_data.get("created_at", None),
            "updated_at": ticket_data.get("updated_at", None),
            "cancel_reason": ticket_data.get("cancel_reason", ""),
        }

        tickets.append(ticket)

    # Trả về danh sách vé
    return tickets

@app.delete("/tickets/{ticket_id}", response_model=Dict)
async def delete_ticket(ticket_id: str):
    """
    API để xóa một vé.
    Trước khi xóa, thêm điểm thưởng vào tài khoản người dùng dựa trên giá vé.
    """
    # Lấy thông tin vé từ Firestore
    ticket_ref = db.collection('tickets').document(ticket_id)
    ticket = ticket_ref.get()

    if not ticket.exists:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket_data = ticket.to_dict()
    user_id = ticket_data["user_id"]
    price = ticket_data["price"]

    # Tính điểm thưởng
    result = int(price / 20000)

    # Cập nhật điểm của người dùng
    user_ref = db.collection('users').document(user_id)
    user = user_ref.get()

    if not user.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = user.to_dict()
    updated_points = user_data.get("point", 0) + result
    user_ref.update({"point": updated_points})

    # Xóa vé
    ticket_ref.delete()

    return {"message": f"Ticket {ticket_id} deleted successfully", "points_added": result}


# Model cho Login
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    user_id: str
    name: str
    email: str
    is_admin: bool

# 13. API Đăng Nhập
@app.post("/users/login", response_model=LoginResponse)
async def login_user(credentials: LoginRequest):
    """
    API đăng nhập cho người dùng.
    Xác thực email và mật khẩu, trả về thông tin người dùng nếu đăng nhập thành công.
    """
    # Truy vấn người dùng từ Firestore dựa trên email
    users_ref = db.collection('users')
    user_query = users_ref.where('email', '==', credentials.email).stream()

    user = next(user_query, None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = user.to_dict()

    # Kiểm tra mật khẩu
    if user_data['password'] != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Trả về thông tin người dùng
    return LoginResponse(
        user_id=user.id,
        name=user_data['name'],
        email=user_data['email'],       
        is_admin=user_data['is_admin']
    )

# 14. API Cập Nhật Thông Tin Người Dùng
@app.put("/users/{user_id}", response_model=Dict)
async def update_user_info(user_id: str, updates: Dict):
    """
    API để người dùng cập nhật thông tin cá nhân của mình.
    """
    user_ref = db.collection('users').document(user_id)
    user = user_ref.get()

    if not user.exists:
        raise HTTPException(status_code=404, detail="User not found")

    # Loại bỏ các trường không được phép chỉnh sửa
    restricted_fields = ["email", "password", "is_admin"]
    updates = {key: value for key, value in updates.items() if key not in restricted_fields}

    # Cập nhật thông tin
    user_ref.update(updates)

    return {"message": f"User {user_id} updated successfully", "updated_fields": updates}

#Dashboard
class MovieStats(BaseModel):
    movie_id: str
    movie_title: str
    revenue: int
    tickets_sold: int
    
@app.get("/stats/users")
async def get_new_users(start_date: datetime, end_date: datetime):
    users_ref = db.collection("users")
    query = users_ref.where("created_at", ">=", start_date).where("created_at", "<=", end_date)
    users = query.stream()

    # Chuyển đổi múi giờ
    utc = pytz.utc
    local_tz = pytz.timezone("Asia/Bangkok")  # Thay đổi thành múi giờ mong muốn (UTC+7)

    grouped_data = {}
    for user in users:
        user_data = user.to_dict()
        created_at = user_data["created_at"].replace(tzinfo=utc).astimezone(local_tz)
        created_date = created_at.date()  # Chỉ lấy phần ngày
        if created_date not in grouped_data:
            grouped_data[created_date] = 0
        grouped_data[created_date] += 1

    result = [{"date": date.isoformat(), "count": count} for date, count in grouped_data.items()]
    result.sort(key=lambda x: x["date"])
    return result

# Get revenue and tickets sold by movie within a time range
@app.get("/stats/movies")
async def get_movie_stats(start_date: datetime, end_date: datetime):
    tickets_ref = db.collection("tickets")
    query = tickets_ref.where("created_at", ">=", start_date).where("created_at", "<=", end_date)
    tickets = query.stream()

    stats = {}
    for ticket in tickets:
        data = ticket.to_dict()
        movie_id = data["movie_id"]
        if movie_id not in stats:
            stats[movie_id] = {
                "movie_title": data["movie_title"],
                "revenue": 0,
                "tickets_sold": 0,
            }
        stats[movie_id]["revenue"] += data["price"]
        stats[movie_id]["tickets_sold"] += 1

    return {"stats": list(stats.values())}


#15. API Cập Nhật Mật Khẩu
class PasswordUpdateRequest(BaseModel):
    old_password: str
    new_password: str

@app.put("/users/{user_id}/update-password")
async def update_password(user_id: str, password_data: PasswordUpdateRequest):
    """
    API để người dùng thay đổi mật khẩu.
    """
    user_ref = db.collection('users').document(user_id)
    user = user_ref.get()

    if not user.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = user.to_dict()

    # Kiểm tra mật khẩu cũ
    if user_data["password"] != password_data.old_password:
        raise HTTPException(status_code=400, detail="Incorrect old password")

    # Cập nhật mật khẩu mới
    user_ref.update({"password": password_data.new_password})

    return {"message": "Password updated successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
