const express = require("express");
const cors = require("cors");
const { Kafka } = require("kafkajs");

const app = express();
const PORT = 5000;

// Middleware
app.use(
  cors({
    origin: "http://localhost:5173", // Allow requests from your frontend
    methods: ["GET", "POST", "OPTIONS"],
    allowedHeaders: ["Content-Type"],
  })
);
app.use(express.json()); // Parses application/json

// Kafka setup
const kafka = new Kafka({
  clientId: "apache-log-producer",
  brokers: ["localhost:9093"], // Match your Kafka setup
});
const producer = kafka.producer();

// Route to receive Apache logs
app.post("/send-log", async (req, res) => {
  const { log } = req.body;

  if (!log || typeof log !== "string") {
    return res.status(400).send("Invalid log format");
  }

  try {
    await producer.send({
      topic: "raw_logs",
      messages: [{ value: log }],
    });

    console.log("✅ Apache log sent to Kafka:", log);
    res.status(200).send("Log sent successfully!");
  } catch (error) {
    console.error("❌ Error sending log to Kafka:", error.message);
    res.status(500).send("Error sending log");
  }
});

// Start server
app.listen(PORT, async () => {
  await producer.connect();
  console.log(`🚀 Server listening at http://localhost:${PORT}`);
});
