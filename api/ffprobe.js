// /api/ffprobe.js

import ffmpegPath from 'ffmpeg-static';
import ffmpeg from 'fluent-ffmpeg';
import { PassThrough } from 'stream';
import ytdl from 'ytdl-core';

export const config = {
  api: {
    bodyParser: false,
  },
};

ffmpeg.setFfmpegPath(ffmpegPath);

export default async function handler(req, res) {
  const { url } = req.query;

  if (!url) {
    return res.status(400).json({ error: 'Missing ?url=...' });
  }

  try {
    let videoStream;

    if (url.includes('googlevideo.com')) {
      const response = await fetch(url, {
        /*
        headers: {
          'User-Agent': 'Mozilla/5.0',
          'Referer': 'https://www.youtube.com',
        },*/
        headers: {
          'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
            '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
          'Referer': 'https://www.youtube.com/',
          'Accept': '*/*',
          'Accept-Language': 'en-US,en;q=0.9',
        }
      });

      if (!response.ok) {
        return res.status(403).json({ error: 'Failed to fetch GoogleVideo URL', status: response.status });
      }

      const buffer = await response.arrayBuffer();
      videoStream = new PassThrough();
      videoStream.end(Buffer.from(buffer));
    } else if (ytdl.validateURL(url)) {
      videoStream = ytdl(url, { quality: 'highestvideo' });
    } else {
      return res.status(400).json({ error: 'Unsupported or invalid video URL' });
    }

    ffmpeg(videoStream).ffprobe((err, data) => {
      if (err) {
        console.error('[ffprobe error]', err);
        return res.status(500).json({ error: 'ffprobe failed', details: err.message });
      }

      const video = data.streams.find(s => s.codec_type === 'video');
      if (!video) {
        return res.status(404).json({ error: 'No video stream found' });
      }

      const profile = String(video.profile || '00').padStart(2, '0');
      const level = String(video.level || '00').padStart(2, '0');
      const bitDepth = String(video.bits_per_raw_sample || '08').padStart(2, '0');
      const fullCodec = `vp09.${profile}.${level}.${bitDepth}`;

      return res.status(200).json({
        codec_name: video.codec_name,
        profile: video.profile,
        level: video.level,
        bitDepth: video.bits_per_raw_sample,
        fullCodec,
      });
    });
  } catch (error) {
    console.error('[Handler error]', error);
    return res.status(500).json({ error: 'Internal Server Error', details: error.message });
  }
}


/*
import ffmpegPath from 'ffmpeg-static';
import ffmpeg from 'fluent-ffmpeg';
import { writeFile, readFile, unlink } from 'fs/promises';
import { tmpdir } from 'os';
import { join } from 'path';

export const config = {
  api: {
    bodyParser: false, // disable body parser for binary responses
  },
};

export default async function handler(req, res) {
  const { url } = req.query;

  if (!url) {
    return res.status(400).json({ error: 'Missing video URL (?url=...)' });
  }

  try {
    // Temp input/output paths
    const inputPath = join(tmpdir(), `input-${Date.now()}.webm`);
    const outputPath = join(tmpdir(), `output-${Date.now()}.webm`);

    // Fetch and save the video
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Failed to fetch video. Status: ${response.status}`);
    const buffer = await response.arrayBuffer();
    await writeFile(inputPath, Buffer.from(buffer));

    // Trim using ffmpeg
    await new Promise((resolve, reject) => {
      ffmpeg(inputPath)
        .setFfmpegPath(ffmpegPath)
        .outputOptions('-t', '2')
        .output(outputPath)
        .on('end', resolve)
        .on('error', reject)
        .run();
    });

    const outputBuffer = await readFile(outputPath);

    // Clean up
    await unlink(inputPath);
    await unlink(outputPath);

    // Return result
    res.setHeader('Content-Type', 'video/webm');
    res.setHeader('Content-Disposition', 'inline; filename="clip.webm"');
    return res.send(outputBuffer);

  } catch (err) {
    console.error('[FFmpeg Error]', err);
    return res.status(500).json({ error: 'FFmpeg failed', details: err.message });
  }
}

*/

/*
import { spawn } from "child_process";
import ffmpegPath from "ffmpeg-static";

export default async function handler(req, res) {
  const videoUrl = req.query.url;
  if (!videoUrl) return res.status(400).json({ error: "Missing video URL" });

  const args = [
    "-i", videoUrl,
    "-t", "2",
    "-f", "webm",
    "-y", "/tmp/sample.webm"
  ];

  const ffmpeg = spawn(ffmpegPath, args);

  let stderr = "";
  ffmpeg.stderr.on("data", data => stderr += data.toString());

  ffmpeg.on("close", (code) => {
    if (code !== 0) {
      return res.status(500).json({ error: "ffmpeg failed", stderr });
    }
    res.status(200).json({ message: "Success", stderr });
  });
}
  */
