import ctypes.wintypes
import pathlib

import aiofiles

from src.config import Config
from src.logger import Logger


def get_video_path():
    """
    获取系统中视频文件夹路径

    Returns:
        Path: 视频文件夹路径
    """
    buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(None, 14, None, 0, buf)
    return pathlib.Path(buf.value)


_video_folder_path = get_video_path()


class VideoIO:
    """对视频文件的输入输出"""

    _instance = None
    logger = Logger(__name__)
    _cfg = Config()

    # 单例模式
    def __new__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kw)
        return cls._instance

    def _get_ts_file_paths(self, episode_name: str):
        self.cwd = self.anime_folder_path / episode_name
        ts_file_paths = (
            path for path in self.cwd.iterdir() if path.suffix == ".ts"
        )
        return ts_file_paths

    def _create_folder(self, _folder_name_or_path: pathlib.Path | str = None):
        """
        Args:
            _folder_name_or_path (pathlib.Path | str, optional): \
                文件夹名称或路径. Defaults to None.
        """

        anime_name = self._cfg.config["common"]["anime_name"]
        self.anime_folder_path = _video_folder_path / anime_name
        """
        # HACK 这里有点投机取巧了，我慢慢讲
        起因是这样，原先以上两行代码在__init__方法中。
        当初始化代码时，Config类会直接读取配置文件，将anime_name设置为之前的名称
        即使使用命令行修改后，Config.config中的anime_name并没有更新。
        以至于创建文件夹时，仍然使用旧的名称，名称错误

        现在，VideoIO会惰性初始化self.anime_folder_path，可以解决这个问题
        前提是你需要调用一遍方法来创建文件夹
        """
        anime_folder_path = self.anime_folder_path
        if _folder_name_or_path:
            anime_folder_path /= _folder_name_or_path
        if not anime_folder_path.is_dir():
            anime_folder_path.mkdir()
            self.logger.info(
                f"Folder [{anime_folder_path}] is created successfully."
            )
        else:
            self.logger.warning(f"Folder [{anime_folder_path}] already exists.")

    def create_anime_folder(self):
        self._create_folder()

    def create_episode_folder(self, episode_name: str):
        self._create_folder(episode_name)

    async def merge_ts_files(self, episode_name):
        """合并ts文件为mp4文件"""
        paths = self._get_ts_file_paths(episode_name)
        async with aiofiles.open(
            self.cwd / f"{episode_name}.mp4", "wb"
        ) as parent_fp:
            for path in paths:
                async with aiofiles.open(path, "rb") as fp:
                    text = await fp.read()
                    await parent_fp.write(text)
        self.logger.info(
            f"Merge ts files to [{self.cwd / f'{episode_name}.mp4'}] successfully." #noqa: E501
        )

    async def save_file(self, path, content):
        """保存文件"""
        async with aiofiles.open(path, "wb") as fp:
            await fp.write(content)

    def clean_up(self, episode_name):
        """清理临时文件"""
        paths = self._get_ts_file_paths(episode_name)
        for path in paths:
            path.unlink()
        self.logger.info(
            f"Clean up temporary files in [{self.cwd}] successfully."
        )
