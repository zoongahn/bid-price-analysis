import os
import shutil

# 현재 스크립트 파일이 위치한 디렉토리를 프로젝트 루트로 간주
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 삭제할 디렉토리 목록
directories = ['logs', 'fetch_record']

for dirname in directories:
	target_dir = os.path.join(project_root, dirname)
	if os.path.isdir(target_dir):
		print(f"Deleting directory: {target_dir}")
		shutil.rmtree(target_dir)
