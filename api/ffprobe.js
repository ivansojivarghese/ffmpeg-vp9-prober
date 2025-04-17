// /api/ffprobe.js
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
