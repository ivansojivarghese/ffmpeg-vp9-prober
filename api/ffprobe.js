
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
