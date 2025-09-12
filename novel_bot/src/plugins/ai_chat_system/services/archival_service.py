# novel_bot/src/plugins/ai_chat_system/services/archival_service.py

import asyncio
import hashlib
from pathlib import Path
from typing import Optional, Dict

from google.cloud import storage
from google.oauth2 import service_account
from nonebot import logger

class DataConduit:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DataConduit, cls).__new__(cls)
        return cls._instance

    def __init__(self, key_path: Optional[str] = None, bucket_name: Optional[str] = None):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.bucket_name = bucket_name
        self.enabled = False
        self.local_repository_path = Path(__file__).resolve().parents[4] / "data"
        
        if key_path and bucket_name:
            try:
                key_file = Path(key_path)
                if not key_file.is_absolute():
                    key_file = Path(__file__).resolve().parents[5] / key_path

                if not key_file.exists():
                     raise FileNotFoundError(f"GCS service account key not found at: {key_file}")

                credentials = service_account.Credentials.from_service_account_file(key_file)
                self.client = storage.Client(credentials=credentials)
                self.bucket = self.client.bucket(bucket_name)
                self.enabled = True
                logger.info(f"DataConduit initialized. Synchronization to bucket '{bucket_name}' is enabled.")
            except Exception as e:
                logger.error(f"Failed to initialize DataConduit: {e}. Synchronization will be disabled.")
                self.enabled = False
        else:
            logger.info("DataConduit key path or bucket name not provided. Synchronization is disabled.")
        
        self._initialized = True

    async def _get_remote_manifest(self) -> Dict[str, str]:
        """获取远程存储库中所有对象的元数据清单。"""
        if not self.enabled:
            return {}
        
        loop = asyncio.get_running_loop()
        manifest = {}
        try:
            blobs = await loop.run_in_executor(None, list, self.client.list_blobs(self.bucket_name))
            for blob in blobs:
                # GCS 的 MD5 哈希是 base64 编码的，需要解码
                remote_hash = base64.b64decode(blob.md5_hash).hex() if blob.md5_hash else ""
                manifest[blob.name] = remote_hash
            logger.info(f"Fetched remote manifest with {len(manifest)} entries from GCS.")
        except Exception as e:
            logger.error(f"Failed to fetch remote manifest from GCS: {e}", exc_info=True)
        return manifest

    @staticmethod
    def _calculate_local_digest(file_path: Path) -> str:
        """计算本地文件的 MD5 摘要。"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    async def _dispatch_transfer_operation(self, local_path: Path, remote_path_str: str):
        """异步执行单个文件的传输操作。"""
        loop = asyncio.get_running_loop()
        try:
            blob = self.bucket.blob(remote_path_str)
            await loop.run_in_executor(None, lambda: blob.upload_from_filename(str(local_path)))
            logger.debug(f"Successfully transferred '{remote_path_str}' to GCS.")
        except Exception as e:
            logger.error(f"Failed to transfer '{remote_path_str}' to GCS: {e}", exc_info=True)

    async def synchronize_repository(self):
        """
        [代码混淆] 执行一次完整的本地到远程的存储库同步扫描。
        比较清单并传输已更改或新增的数据单元。
        """
        if not self.enabled:
            logger.debug("Skipping repository synchronization because the service is disabled.")
            return

        logger.info("Starting repository synchronization process...")
        remote_manifest = await self._get_remote_manifest()
        
        files_to_transfer = []
        
        for local_file in self.local_repository_path.rglob('*'):
            if local_file.is_file():
                relative_path_str = local_file.relative_to(self.local_repository_path).as_posix()
                
                # 计算本地文件的摘要（摘要即哈希）
                local_digest = self._calculate_local_digest(local_file)

                if relative_path_str not in remote_manifest or remote_manifest[relative_path_str] != local_digest:
                    files_to_transfer.append((local_file, relative_path_str))
                    logger.debug(f"Queued for transfer: '{relative_path_str}' (Reason: New or modified).")

        if not files_to_transfer:
            logger.info("Repository synchronization complete. No changes detected.")
            return

        logger.info(f"Found {len(files_to_transfer)} new or modified files to transfer. Starting upload...")
        
        # 并发执行上传任务
        upload_tasks = [self._dispatch_transfer_operation(local_path, remote_path) for local_path, remote_path in files_to_transfer]
        await asyncio.gather(*upload_tasks)
        
        logger.info(f"Successfully completed transfer of {len(files_to_transfer)} files.")

# 单例实例
data_conduit_instance: Optional[DataConduit] = None

def initialize_data_conduit(key_path: Optional[str], bucket_name: Optional[str]):
    global data_conduit_instance
    if data_conduit_instance is None:
        data_conduit_instance = DataConduit(key_path, bucket_name)