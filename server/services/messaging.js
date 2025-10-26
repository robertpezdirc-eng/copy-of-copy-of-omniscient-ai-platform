// server/services/messaging.js
// Univerzalna storitev sporočanja za Kafka in RabbitMQ (AMQP)
import { Kafka, logLevel } from 'kafkajs';
import amqplib from 'amqplib';

let kafkaProducer = null;
let kafkaClient = null;
let rabbitConn = null;
let rabbitChannel = null;

const messaging = {
  async initKafka() {
    try {
      if (kafkaProducer) return true;
      const brokersEnv = process.env.KAFKA_BROKERS || process.env.KAFKA_URL || '';
      const brokers = brokersEnv ? brokersEnv.split(',').map(b => b.trim()) : ['localhost:9092'];
      const clientId = process.env.KAFKA_CLIENT_ID || 'omni-brain';
      kafkaClient = new Kafka({ clientId, brokers, logLevel: logLevel.NOTHING });
      kafkaProducer = kafkaClient.producer();
      await kafkaProducer.connect();
      console.log(`✅ Kafka producer connected (clientId=${clientId}, brokers=${brokers.join(',')})`);
      return true;
    } catch (err) {
      console.warn('⚠️ Kafka init failed:', err.message);
      kafkaProducer = null;
      kafkaClient = null;
      return false;
    }
  },

  async initRabbit() {
    try {
      if (rabbitChannel) return true;
      const url = process.env.RABBITMQ_URL || 'amqp://localhost';
      rabbitConn = await amqplib.connect(url);
      rabbitChannel = await rabbitConn.createChannel();
      console.log(`✅ RabbitMQ channel connected (${url})`);
      return true;
    } catch (err) {
      console.warn('⚠️ RabbitMQ init failed:', err.message);
      rabbitConn = null;
      rabbitChannel = null;
      return false;
    }
  },

  async publishKafka(topic, message) {
    try {
      if (!kafkaProducer) {
        const ok = await this.initKafka();
        if (!ok) throw new Error('Kafka not available');
      }
      const payload = typeof message === 'string' ? message : JSON.stringify(message);
      await kafkaProducer.send({ topic, messages: [{ value: payload }] });
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  },

  async publishRabbit(queue, message) {
    try {
      if (!rabbitChannel) {
        const ok = await this.initRabbit();
        if (!ok) throw new Error('RabbitMQ not available');
      }
      const payload = Buffer.from(
        typeof message === 'string' ? message : JSON.stringify(message)
      );
      await rabbitChannel.assertQueue(queue, { durable: true });
      const ok = rabbitChannel.sendToQueue(queue, payload, { persistent: true });
      return { success: ok };
    } catch (err) {
      return { success: false, error: err.message };
    }
  },

  async health() {
    return {
      kafka: !!kafkaProducer,
      rabbitmq: !!rabbitChannel,
      kafka_brokers: (process.env.KAFKA_BROKERS || process.env.KAFKA_URL || 'localhost:9092'),
      rabbit_url: (process.env.RABBITMQ_URL || 'amqp://localhost'),
      timestamp: new Date().toISOString()
    };
  },

  config() {
    return {
      KAFKA_BROKERS: process.env.KAFKA_BROKERS || process.env.KAFKA_URL || 'localhost:9092',
      KAFKA_CLIENT_ID: process.env.KAFKA_CLIENT_ID || 'omni-brain',
      RABBITMQ_URL: process.env.RABBITMQ_URL || 'amqp://localhost'
    };
  }
};

export default messaging;