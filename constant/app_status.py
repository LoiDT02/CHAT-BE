from enum import Enum
from starlette import status


class AppStatus(Enum):
    SUCCESS = status.HTTP_200_OK, 'SUCCESS', 'Thành công!'

    ERROR_400_BAD_REQUEST = status.HTTP_400_BAD_REQUEST, 'BAD_REQUEST', 'Yêu cầu không hợp lệ.'
    ERROR_400_USER_ALREADY_EXISTS = status.HTTP_400_BAD_REQUEST, 'BAD_REQUEST', 'Người dùng đã tồn tại.'
    ERROR_400_INVALID_USERNAME_PASSWORD = status.HTTP_400_BAD_REQUEST, 'INVALID_USERNAME_PASSWORD', ('Tên người dùng '
                                                                                                     'hoặc mật khẩu '
                                                                                                     'không hợp lệ.')
    ERROR_400_INVALID_TOKEN = status.HTTP_400_BAD_REQUEST, 'INVALID_TOKEN', 'Mã truy cập không hợp lệ.'
    ERROR_400_INVALID_OBJECT_ID = status.HTTP_400_BAD_REQUEST, 'INVALID_OBJECT_ID', '{description} không phải là một ObjectId hợp lệ.'
    ERROR_400_INVALID_DATA = status.HTTP_400_BAD_REQUEST, 'INVALID_DATA', 'Dữ liệu vào không hợp lệ: {description}'
    ERROR_400_INVALID_DATA_IMPORT = status.HTTP_400_BAD_REQUEST, 'INVALID_DATA_IMPORT', '{description}'
    ERROR_400_NOTHING_TO_UPDATE = status.HTTP_400_BAD_REQUEST, 'NOTHING_TO_UPDATE', 'Không có gì để cập nhật'
    ERROR_400_PARTY_MEMBERSHIP_NUMBER_UNIQUE = status.HTTP_400_BAD_REQUEST, 'PARTY_MEMBERSHIP_NUMBER_UNIQUE', ('Số thẻ '
                                                                                                               'đảng '
                                                                                                               'không '
                                                                                                               'thể '
                                                                                                               'bị '
                                                                                                               'trùng '
                                                                                                               'lặp')
    ERROR_400_DOCUMENT_NUMBER_UNIQUE = status.HTTP_400_BAD_REQUEST, 'DOCUMENT_NUMBER_UNIQUE', 'Số của tài liệu không thể bị trùng lặp'
    ERROR_400_EXTERNAL_DOCUMENT_NUMBER_UNIQUE = status.HTTP_400_BAD_REQUEST, 'DOCUMENT_NUMBER_UNIQUE', 'Số của tài liệu bên ngoài không thể bị trùng lặp'

    ERROR_400_CANNOT_READ_FILE_EXCEL = status.HTTP_400_BAD_REQUEST, 'CANNOT_READ_FILE', 'Không thể đọc tệp Excel'
    ERROR_400_CANNOT_READ_COLUMN_FILE_EXCEL = status.HTTP_400_BAD_REQUEST, 'CANNOT_READ_COLUMN_FILE', (
        'File không chứa thông tin về đảng viên.')
    ERROR_400_UNSUPPORTED_FORMAT = status.HTTP_400_BAD_REQUEST, 'UN_SUPPORT_FORMAT', 'Định dạng tệp không được hỗ trợ.'
    ERROR_400_MEETING_HAS_REPORT_SENT = status.HTTP_400_BAD_REQUEST, 'REPORT_SENT', 'Không thể cập nhật khi báo cáo đã được gửi.'
    ERROR_400_MEETING_HAS_ENDED = status.HTTP_400_BAD_REQUEST, 'HAS_ENDED', 'Không thể cập nhật sau khi cuộc họp kết thúc.'
    ERROR_400_MEETING_NOT_ENDED = status.HTTP_400_BAD_REQUEST, 'NOT_ENDED', 'Không thể cập nhật báo cáo và báo cáo đã gửi trước khi cuộc họp kết thúc.'
    ERROR_400_INVALID_URL = status.HTTP_400_BAD_REQUEST, 'INVALID_URL', 'Đường dẫn chứa các ký tự không được hỗ trợ.'
    ERROR_400_CELL_ALREADY_EXISTS = status.HTTP_400_BAD_REQUEST, 'CELL_ALREADY_EXISTS', ("Chi bộ có tên '{name}' đã "
                                                                                         "tồn tại.")

    ERROR_400_PARTY_MEMBER_ARE_NOT_AT_THE_MANAGEMENT_LEVEL = status.HTTP_400_BAD_REQUEST, 'NOT_AT_THE_MANAGEMENT_LEVEL', 'Đảng viên không thuộc cấp quản lý nên không thể tạo văn bản.'
    ERROR_400_DISTRIBUTION_ALREADY_EXISTS = status.HTTP_400_BAD_REQUEST, 'ALREADY_EXISTS', 'Phân bổ văn bản đã tồn tại.'
    ERROR_400_ISSUE_ALREADY_CLOSED = status.HTTP_400_BAD_REQUEST, 'ALREADY_CLOSED', 'Vấn đề đã được đóng.'
    ERROR_400_ISSUE_ALREADY_REOPENED = status.HTTP_400_BAD_REQUEST, 'ALREADY_REOPENED', 'Vấn đề đã được mở lại.'

    HTTP_401_USER_NOT_ACTIVE = status.HTTP_401_UNAUTHORIZED, 'UNAUTHORIZED', 'Người dùng chưa được kích hoạt.'
    ERROR_401_EXPIRED_TOKEN = status.HTTP_401_UNAUTHORIZED, 'EXPIRED TOKEN', 'Mã truy cập đã hết hạn.'

    ERROR_403_FORBIDDEN = status.HTTP_403_FORBIDDEN, 'FORBIDDEN', 'Bạn không được phép thực hiện hành động này.'

    ERROR_404_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', ('Không tìm thấy tài nguyên yêu cầu. Vui lòng đảm '
                                                                   'bảo rằng URL hoặc yêu cầu là chính xác và tương '
                                                                   'ứng với một tài nguyên hiện có trong hệ thống của '
                                                                   'chúng tôi. Nếu bạn tin rằng đây là lỗi, '
                                                                   'xin vui lòng liên hệ với đội hỗ trợ của chúng tôi '
                                                                   'để được hỗ trợ thêm. Chúng tôi xin lỗi vì bất kỳ '
                                                                   'sự bất tiện nào.')
    ERROR_404_USER_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Không tìm thấy người dùng.'
    ERROR_404_MEETING_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Không tìm thấy cuộc họp.'
    ERROR_404_ATTENDANCE_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Không tìm thấy danh sách tham dự.'
    ERROR_404_NOTIFICATION_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Không tìm thấy thông báo với ID: {description}'
    ERROR_404_CELL_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Không tìm thấy chi bộ.'
    ERROR_404_MEMBERSHIP_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Không tìm thấy thành viên.'
    ERROR_404_MEMBERSHIP_213_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Không tìm thấy thành viên 213.'
    ERROR_404_FILTER_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Không tìm thấy bộ lọc.'
    ERROR_404_MEMBERSHIP_HISTORY_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Không tìm thấy lịch sử thành viên.'
    ERROR_404_ORIGIN_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Không tìm thấy nơi ban hành.'
    ERROR_404_WARD_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Không tìm thấy phường.'
    ERROR_404_DOCUMENT_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Không tìm thấy tài liệu.'
    ERROR_404_EXTERNAL_DOCUMENT_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Không tìm thấy tài liệu bên ngoài.'
    ERROR_404_DISTRIBUTION_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Phân bổ văn bản không tồn tại.'
    ERROR_404_EXTERNAL_DISTRIBUTION_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Phân bổ văn bản bên ngoài không tồn tại.'
    ERROR_404_ISSUE_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Không tìm thấy vấn đề.'
    ERROR_404_COMMENT_NOT_FOUND = status.HTTP_404_NOT_FOUND, 'NOT_FOUND', 'Không tìm thấy bình luận.'

    ERROR_405_METHOD_NOT_ALLOWED = status.HTTP_405_METHOD_NOT_ALLOWED, 'METHOD_NOT_ALLOWED', ('Bạn không được phép '
                                                                                              'thực hiện hành động '
                                                                                              'này.')
    ERROR_405_METHOD_NOT_ALLOWED_BY_OPA = status.HTTP_405_METHOD_NOT_ALLOWED, 'METHOD_NOT_ALLOWED', ('Bạn không được '
                                                                                                     'phép thực hiện '
                                                                                                     'hành động này '
                                                                                                     'do:\n{'
                                                                                                     'description}')

    ERROR_429_TOO_MANY_REQUESTS = status.HTTP_429_TOO_MANY_REQUESTS, 'TOO_MANY_REQUESTS', 'Đăng nhập quá nhiều lần. Vui lòng thử lại sau.'

    ERROR_500_INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR, 'INTERNAL_SERVER_ERROR', ('Đã xảy ra lỗi '
                                                                                                       'máy chủ nội '
                                                                                                       'bộ. Đây là '
                                                                                                       'vấn đề từ '
                                                                                                       'phía chúng '
                                                                                                       'tôi, '
                                                                                                       'và chúng tôi '
                                                                                                       'đang tích cực '
                                                                                                       'làm việc để '
                                                                                                       'giải quyết '
                                                                                                       'nó. Chúng tôi '
                                                                                                       'xin lỗi vì '
                                                                                                       'bất kỳ sự bất '
                                                                                                       'tiện nào điều '
                                                                                                       'này có thể đã '
                                                                                                       'gây ra. Nếu '
                                                                                                       'bạn cần hỗ '
                                                                                                       'trợ ngay lập '
                                                                                                       'tức hoặc có '
                                                                                                       'bất kỳ câu '
                                                                                                       'hỏi nào, '
                                                                                                       'xin vui lòng '
                                                                                                       'liên hệ với '
                                                                                                       'đội hỗ trợ '
                                                                                                       'của chúng '
                                                                                                       'tôi, '
                                                                                                       'và họ sẽ hỗ '
                                                                                                       'trợ bạn giải '
                                                                                                       'quyết vấn đề. '
                                                                                                       'Cảm ơn bạn đã '
                                                                                                       'kiên nhẫn.')

    @property
    def status_code(self):
        return self.value[0]

    @property
    def name(self):
        return self.value[1]

    @property
    def message(self):
        return self.value[2]
