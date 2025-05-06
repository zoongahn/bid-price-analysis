from common.utils import *
from common.init_mongodb import init_mongodb_via_ssh

server, db = init_mongodb_via_ssh()

collection = db["api_list"]

results = collection.find({"service_name": "입찰공고정보서비스"},
                          {"operations.오퍼레이션명(국문)": 1, "_id": 0})

operation_titles = [op['오퍼레이션명(국문)'] for op in results[0]['operations']]

print(operation_titles)

csv_file_name = f"{operation_titles[0]}.csv"
csv_file_path = os.path.join(get_project_root(), "api_info", "operation_fields", csv_file_name)

ld = parse_csv_to_listdict(csv_file_path)

print(ld)

server.stop()
