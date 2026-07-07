# src/services/video_processor.py
import subprocess
import tempfile
import os
from typing import Tuple, Dict, Any, Optional
import json


class VideoProcessor:
    async def process(
            self,
            input_data: bytes,
            quality: str = "medium",
            video_id: Optional[str] = None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Обработка видео с помощью FFmpeg"""

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_input:
            tmp_input.write(input_data)
            input_path = tmp_input.name

        output_path = f"/tmp/processed_{video_id}.mp4" if video_id else "/tmp/processed.mp4"

        try:
            quality_params = {
                'low': ['-vf', 'scale=640:360', '-b:v', '500k'],
                'medium': ['-vf', 'scale=1280:720', '-b:v', '1500k'],
                'high': ['-vf', 'scale=1920:1080', '-b:v', '4000k']
            }

            cmd = [
                'ffmpeg',
                '-i', input_path,
                *quality_params.get(quality, quality_params['medium']),
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")

            with open(output_path, 'rb') as f:
                output_data = f.read()

            metadata = self._get_metadata(output_path)

            return output_data, metadata

        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def _get_metadata(self, video_path: str) -> Dict[str, Any]:
        """Получение метаданных видео"""
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return {}

        data = json.loads(result.stdout)

        metadata: Dict[str, Any] = {}
        if 'format' in data:
            metadata['duration'] = float(data['format'].get('duration', 0))

        if 'streams' in data:
            video_stream = next(
                (s for s in data['streams'] if s.get('codec_type') == 'video'),
                None
            )
            if video_stream:
                metadata['width'] = int(video_stream.get('width', 0))
                metadata['height'] = int(video_stream.get('height', 0))
                r_frame_rate = video_stream.get('r_frame_rate', '0/1')
                if '/' in r_frame_rate:
                    num, den = r_frame_rate.split('/')
                    metadata['fps'] = float(num) / float(den) if float(den) != 0 else 0.0
                else:
                    metadata['fps'] = float(r_frame_rate)
                metadata['codec'] = video_stream.get('codec_name')

        return metadata