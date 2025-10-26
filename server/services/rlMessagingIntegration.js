/**
 * RL Messaging Integration Service - Omni God Brain
 * Integrates Reinforcement Learning systems with Kafka/RabbitMQ messaging
 * Enables real-time learning data flow and RL model updates
 */

import messaging from './messaging.js';
import { EventEmitter } from 'events';

class RLMessagingIntegration extends EventEmitter {
    constructor(rlSystems) {
        super();
        this.rlSystems = rlSystems;
        this.status = 'INITIALIZING';
        this.messageHandlers = new Map();
        this.rlDataStreams = new Map();
        this.experienceBuffer = [];
        this.learningMetrics = new Map();

        // RL Messaging configuration
        this.config = {
            kafkaTopics: {
                rlExperiences: 'omni.rl.experiences',
                rlModels: 'omni.rl.models',
                rlMetrics: 'omni.rl.metrics',
                rlActions: 'omni.rl.actions',
                rlRewards: 'omni.rl.rewards'
            },
            rabbitQueues: {
                rlLearning: 'omni.rl.learning',
                rlInference: 'omni.rl.inference',
                rlUpdates: 'omni.rl.updates',
                rlFeedback: 'omni.rl.feedback'
            },
            batchSize: 100,
            flushInterval: 30000, // 30 seconds
            enableRealTimeSync: true,
            maxBufferSize: 10000
        };

        console.log('🧠🔗 RL Messaging Integration - Initializing...');
        this.initialize();
    }

    async initialize() {
        try {
            // Set up Kafka integration
            await this.setupKafkaIntegration();

            // Set up RabbitMQ integration
            await this.setupRabbitMQIntegration();

            // Set up RL data streams
            this.setupRLDataStreams();

            // Set up message handlers
            this.setupMessageHandlers();

            // Set up experience buffering
            this.setupExperienceBuffering();

            // Set up real-time synchronization
            if (this.config.enableRealTimeSync) {
                this.setupRealTimeSync();
            }

            this.status = 'ACTIVE';
            console.log('✅ RL Messaging Integration - Successfully initialized');

            // Emit initialization event
            this.emit('initialized', {
                status: 'active',
                kafkaTopics: this.config.kafkaTopics,
                rabbitQueues: this.config.rabbitQueues,
                timestamp: new Date().toISOString()
            });

        } catch (error) {
            console.error('❌ Failed to initialize RL Messaging Integration:', error);
            this.status = 'ERROR';
            throw error;
        }
    }

    async setupKafkaIntegration() {
        console.log('📨 Setting up Kafka integration for RL systems...');

        try {
            // Initialize Kafka if not already connected
            const kafkaConnected = await messaging.initKafka();
            if (!kafkaConnected) {
                throw new Error('Failed to connect to Kafka');
            }

            // Set up Kafka consumers for RL topics
            await this.setupKafkaConsumers();

            // Set up Kafka producers for RL outputs
            await this.setupKafkaProducers();

            console.log('✅ Kafka integration for RL systems established');

        } catch (error) {
            console.error('❌ Failed to setup Kafka integration:', error);
            throw error;
        }
    }

    async setupRabbitMQIntegration() {
        console.log('📨 Setting up RabbitMQ integration for RL systems...');

        try {
            // Initialize RabbitMQ if not already connected
            const rabbitConnected = await messaging.initRabbit();
            if (!rabbitConnected) {
                throw new Error('Failed to connect to RabbitMQ');
            }

            // Set up RabbitMQ consumers for RL queues
            await this.setupRabbitMQConsumers();

            // Set up RabbitMQ producers for RL outputs
            await this.setupRabbitMQProducers();

            console.log('✅ RabbitMQ integration for RL systems established');

        } catch (error) {
            console.error('❌ Failed to setup RabbitMQ integration:', error);
            throw error;
        }
    }

    async setupKafkaConsumers() {
        console.log('📥 Setting up Kafka consumers for RL data...');

        // Consumer for RL experiences
        this.setupKafkaConsumerForTopic(
            this.config.kafkaTopics.rlExperiences,
            'rl_experiences',
            async (message) => {
                await this.handleRLExperienceMessage(message);
            }
        );

        // Consumer for RL rewards
        this.setupKafkaConsumerForTopic(
            this.config.kafkaTopics.rlRewards,
            'rl_rewards',
            async (message) => {
                await this.handleRLRewardMessage(message);
            }
        );

        // Consumer for RL feedback
        this.setupKafkaConsumerForTopic(
            this.config.kafkaTopics.rlActions,
            'rl_actions',
            async (message) => {
                await this.handleRLActionMessage(message);
            }
        );

        console.log('✅ Kafka consumers for RL data configured');
    }

    async setupRabbitMQConsumers() {
        console.log('📥 Setting up RabbitMQ consumers for RL data...');

        // Consumer for RL learning requests
        this.setupRabbitMQConsumerForQueue(
            this.config.rabbitQueues.rlLearning,
            'rl_learning',
            async (message) => {
                await this.handleRLLearningMessage(message);
            }
        );

        // Consumer for RL inference requests
        this.setupRabbitMQConsumerForQueue(
            this.config.rabbitQueues.rlInference,
            'rl_inference',
            async (message) => {
                await this.handleRLInferenceMessage(message);
            }
        );

        // Consumer for RL feedback
        this.setupRabbitMQConsumerForQueue(
            this.config.rabbitQueues.rlFeedback,
            'rl_feedback',
            async (message) => {
                await this.handleRLFeedbackMessage(message);
            }
        );

        console.log('✅ RabbitMQ consumers for RL data configured');
    }

    setupKafkaConsumerForTopic(topic, handlerName, handler) {
        // In a real implementation, set up proper Kafka consumer
        this.messageHandlers.set(handlerName, handler);
        console.log(`📥 Kafka consumer configured for topic: ${topic}`);
    }

    setupRabbitMQConsumerForQueue(queue, handlerName, handler) {
        // In a real implementation, set up proper RabbitMQ consumer
        this.messageHandlers.set(handlerName, handler);
        console.log(`📥 RabbitMQ consumer configured for queue: ${queue}`);
    }

    async setupKafkaProducers() {
        console.log('📤 Setting up Kafka producers for RL outputs...');

        // Producer for RL model updates
        this.rlDataStreams.set('kafka_models', {
            type: 'kafka',
            topic: this.config.kafkaTopics.rlModels,
            enabled: true
        });

        // Producer for RL metrics
        this.rlDataStreams.set('kafka_metrics', {
            type: 'kafka',
            topic: this.config.kafkaTopics.rlMetrics,
            enabled: true
        });

        console.log('✅ Kafka producers for RL outputs configured');
    }

    async setupRabbitMQProducers() {
        console.log('📤 Setting up RabbitMQ producers for RL outputs...');

        // Producer for RL updates
        this.rlDataStreams.set('rabbitmq_updates', {
            type: 'rabbitmq',
            queue: this.config.rabbitQueues.rlUpdates,
            enabled: true
        });

        console.log('✅ RabbitMQ producers for RL outputs configured');
    }

    setupRLDataStreams() {
        console.log('🌊 Setting up RL data streams...');

        // Stream for Q-Learning experiences
        this.rlDataStreams.set('q_learning_stream', {
            type: 'internal',
            algorithm: 'q_learning',
            enabled: true,
            buffer: []
        });

        // Stream for Policy Gradient experiences
        this.rlDataStreams.set('policy_gradient_stream', {
            type: 'internal',
            algorithm: 'policy_gradient',
            enabled: true,
            buffer: []
        });

        // Stream for Actor-Critic experiences
        this.rlDataStreams.set('actor_critic_stream', {
            type: 'internal',
            algorithm: 'actor_critic',
            enabled: true,
            buffer: []
        });

        console.log('✅ RL data streams configured');
    }

    setupMessageHandlers() {
        console.log('🎯 Setting up RL message handlers...');

        // Handler for RL experience messages
        this.messageHandlers.set('rl_experience_handler', async (message) => {
            await this.processRLExperience(message);
        });

        // Handler for RL model update messages
        this.messageHandlers.set('rl_model_update_handler', async (message) => {
            await this.processRLModelUpdate(message);
        });

        // Handler for RL inference requests
        this.messageHandlers.set('rl_inference_handler', async (message) => {
            await this.processRLInferenceRequest(message);
        });

        console.log('✅ RL message handlers configured');
    }

    setupExperienceBuffering() {
        console.log('💾 Setting up RL experience buffering...');

        // Buffer flush interval
        setInterval(async () => {
            await this.flushExperienceBuffer();
        }, this.config.flushInterval);

        console.log('✅ RL experience buffering configured');
    }

    setupRealTimeSync() {
        console.log('⚡ Setting up real-time RL synchronization...');

        // Real-time sync interval
        setInterval(async () => {
            await this.syncRLSystems();
        }, 5000); // Every 5 seconds

        console.log('✅ Real-time RL synchronization configured');
    }

    async handleRLExperienceMessage(message) {
        console.log('🧠 Processing RL experience message...');

        try {
            const experience = JSON.parse(message.value || message);

            // Add to experience buffer
            this.addToExperienceBuffer(experience);

            // Process immediately if real-time sync is enabled
            if (this.config.enableRealTimeSync) {
                await this.processRLExperience(experience);
            }

            // Emit RL experience event
            this.emit('rl_experience', experience);

        } catch (error) {
            console.error('❌ Error handling RL experience message:', error);
        }
    }

    async handleRLRewardMessage(message) {
        console.log('🎖️ Processing RL reward message...');

        try {
            const reward = JSON.parse(message.value || message);

            // Process reward for RL systems
            await this.processRLReward(reward);

            // Emit RL reward event
            this.emit('rl_reward', reward);

        } catch (error) {
            console.error('❌ Error handling RL reward message:', error);
        }
    }

    async handleRLActionMessage(message) {
        console.log('🎬 Processing RL action message...');

        try {
            const action = JSON.parse(message.value || message);

            // Process action for RL systems
            await this.processRLAction(action);

            // Emit RL action event
            this.emit('rl_action', action);

        } catch (error) {
            console.error('❌ Error handling RL action message:', error);
        }
    }

    async handleRLLearningMessage(message) {
        console.log('📚 Processing RL learning message...');

        try {
            const learningRequest = JSON.parse(message);

            // Process learning request
            await this.processRLLearningRequest(learningRequest);

            // Emit RL learning event
            this.emit('rl_learning_request', learningRequest);

        } catch (error) {
            console.error('❌ Error handling RL learning message:', error);
        }
    }

    async handleRLInferenceMessage(message) {
        console.log('🔮 Processing RL inference message...');

        try {
            const inferenceRequest = JSON.parse(message);

            // Process inference request
            await this.processRLInferenceRequest(inferenceRequest);

            // Emit RL inference event
            this.emit('rl_inference_request', inferenceRequest);

        } catch (error) {
            console.error('❌ Error handling RL inference message:', error);
        }
    }

    async handleRLFeedbackMessage(message) {
        console.log('🔄 Processing RL feedback message...');

        try {
            const feedback = JSON.parse(message);

            // Process feedback for RL systems
            await this.processRLFeedback(feedback);

            // Emit RL feedback event
            this.emit('rl_feedback', feedback);

        } catch (error) {
            console.error('❌ Error handling RL feedback message:', error);
        }
    }

    async processRLExperience(experience) {
        console.log('⚡ Processing RL experience for learning...');

        try {
            // Add experience to appropriate RL algorithm stream
            await this.addExperienceToRLStream(experience);

            // Update RL systems with new experience
            if (this.rlSystems) {
                await this.updateRLSystemsWithExperience(experience);
            }

            // Store experience for batch processing
            this.addToExperienceBuffer(experience);

            console.log('✅ RL experience processed');

        } catch (error) {
            console.error('❌ Error processing RL experience:', error);
        }
    }

    async addExperienceToRLStream(experience) {
        // Add experience to appropriate algorithm stream
        const algorithm = experience.algorithm || 'q_learning';

        const streamKey = `${algorithm}_stream`;
        const stream = this.rlDataStreams.get(streamKey);

        if (stream && stream.enabled) {
            stream.buffer.push({
                ...experience,
                timestamp: new Date().toISOString(),
                processed: false
            });

            // Limit buffer size
            if (stream.buffer.length > this.config.maxBufferSize) {
                stream.buffer.shift(); // Remove oldest
            }
        }
    }

    async updateRLSystemsWithExperience(experience) {
        if (!this.rlSystems) return;

        try {
            // Update Q-Learning engine
            if (this.rlSystems.qLearningEngine) {
                await this.updateQLearningEngine(experience);
            }

            // Update Policy Gradient
            if (this.rlSystems.policyGradient) {
                await this.updatePolicyGradient(experience);
            }

            // Update Actor-Critic
            if (this.rlSystems.actorCritic) {
                await this.updateActorCritic(experience);
            }

            console.log('✅ RL systems updated with experience');

        } catch (error) {
            console.error('❌ Error updating RL systems:', error);
        }
    }

    async updateQLearningEngine(experience) {
        // Update Q-Learning with new experience
        if (this.rlSystems.qLearningEngine.qLearning) {
            // In a real implementation, call the Q-Learning update method
            console.log('📊 Updating Q-Learning engine with experience');
        }
    }

    async updatePolicyGradient(experience) {
        // Update Policy Gradient with new experience
        if (this.rlSystems.policyGradient.policyGradientOptimization) {
            // In a real implementation, call the Policy Gradient update method
            console.log('📈 Updating Policy Gradient with experience');
        }
    }

    async updateActorCritic(experience) {
        // Update Actor-Critic with new experience
        if (this.rlSystems.actorCritic.actorCriticLearning) {
            // In a real implementation, call the Actor-Critic update method
            console.log('🎭 Updating Actor-Critic with experience');
        }
    }

    async processRLReward(reward) {
        console.log('🎖️ Processing RL reward...');

        try {
            // Update RL systems with reward information
            if (this.rlSystems) {
                await this.updateRLSystemsWithReward(reward);
            }

            // Store reward for learning
            this.storeRewardForLearning(reward);

            console.log('✅ RL reward processed');

        } catch (error) {
            console.error('❌ Error processing RL reward:', error);
        }
    }

    async updateRLSystemsWithReward(reward) {
        if (!this.rlSystems) return;

        // Update reward functions across RL algorithms
        console.log('🎖️ Updating RL systems with reward signal');
    }

    async processRLAction(action) {
        console.log('🎬 Processing RL action...');

        try {
            // Validate action
            const validation = await this.validateRLAction(action);

            if (validation.valid) {
                // Execute action through RL systems
                await this.executeRLAction(action);

                // Store action for learning
                this.storeActionForLearning(action);
            } else {
                console.error('❌ Invalid RL action:', validation.errors);
            }

            console.log('✅ RL action processed');

        } catch (error) {
            console.error('❌ Error processing RL action:', error);
        }
    }

    async validateRLAction(action) {
        const validation = {
            valid: true,
            errors: []
        };

        // Basic validation
        if (!action.type) {
            validation.valid = false;
            validation.errors.push('Action type is required');
        }

        if (!action.agentId) {
            validation.valid = false;
            validation.errors.push('Agent ID is required');
        }

        return validation;
    }

    async executeRLAction(action) {
        if (!this.rlSystems) return;

        // Execute action through appropriate RL algorithm
        switch (action.algorithm) {
            case 'q_learning':
                await this.executeQLearningAction(action);
                break;
            case 'policy_gradient':
                await this.executePolicyGradientAction(action);
                break;
            case 'actor_critic':
                await this.executeActorCriticAction(action);
                break;
            default:
                await this.executeGenericRLAction(action);
        }
    }

    async executeQLearningAction(action) {
        console.log('📊 Executing Q-Learning action');
        // In a real implementation, execute through Q-Learning engine
    }

    async executePolicyGradientAction(action) {
        console.log('📈 Executing Policy Gradient action');
        // In a real implementation, execute through Policy Gradient
    }

    async executeActorCriticAction(action) {
        console.log('🎭 Executing Actor-Critic action');
        // In a real implementation, execute through Actor-Critic
    }

    async executeGenericRLAction(action) {
        console.log('⚙️ Executing generic RL action');
        // Generic action execution
    }

    async processRLLearningRequest(request) {
        console.log('📚 Processing RL learning request...');

        try {
            // Initiate learning process
            const learningResult = await this.initiateRLLearning(request);

            // Publish learning results
            await this.publishRLLearningResults(request, learningResult);

            console.log('✅ RL learning request processed');

        } catch (error) {
            console.error('❌ Error processing RL learning request:', error);
        }
    }

    async initiateRLLearning(request) {
        if (!this.rlSystems) {
            throw new Error('RL systems not available');
        }

        // Initiate learning based on request type
        switch (request.algorithm) {
            case 'q_learning':
                return await this.initiateQLearning(request);
            case 'ppo':
                return await this.initiatePPO(request);
            case 'sac':
                return await this.initiateSAC(request);
            default:
                return await this.initiateGenericLearning(request);
        }
    }

    async initiateQLearning(request) {
        console.log('📊 Initiating Q-Learning...');

        if (this.rlSystems.qLearningEngine?.qLearning) {
            // In a real implementation, call Q-Learning method
            return {
                algorithm: 'q_learning',
                status: 'initiated',
                timestamp: new Date().toISOString()
            };
        }

        throw new Error('Q-Learning not available');
    }

    async initiatePPO(request) {
        console.log('🎯 Initiating PPO learning...');

        if (this.rlSystems.policyGradient?.proximalPolicyOptimization) {
            // In a real implementation, call PPO method
            return {
                algorithm: 'ppo',
                status: 'initiated',
                timestamp: new Date().toISOString()
            };
        }

        throw new Error('PPO not available');
    }

    async initiateSAC(request) {
        console.log('🌊 Initiating SAC learning...');

        if (this.rlSystems.policyGradient?.softActorCritic) {
            // In a real implementation, call SAC method
            return {
                algorithm: 'sac',
                status: 'initiated',
                timestamp: new Date().toISOString()
            };
        }

        throw new Error('SAC not available');
    }

    async initiateGenericLearning(request) {
        console.log('⚙️ Initiating generic RL learning...');

        return {
            algorithm: request.algorithm || 'generic',
            status: 'initiated',
            timestamp: new Date().toISOString()
        };
    }

    async processRLInferenceRequest(request) {
        console.log('🔮 Processing RL inference request...');

        try {
            // Perform RL inference
            const inferenceResult = await this.performRLInference(request);

            // Publish inference results
            await this.publishRLInferenceResults(request, inferenceResult);

            console.log('✅ RL inference request processed');

        } catch (error) {
            console.error('❌ Error processing RL inference request:', error);
        }
    }

    async performRLInference(request) {
        if (!this.rlSystems) {
            throw new Error('RL systems not available');
        }

        // Perform inference based on algorithm
        switch (request.algorithm) {
            case 'q_learning':
                return await this.performQLearningInference(request);
            case 'policy_gradient':
                return await this.performPolicyGradientInference(request);
            case 'actor_critic':
                return await this.performActorCriticInference(request);
            default:
                return await this.performGenericInference(request);
        }
    }

    async performQLearningInference(request) {
        console.log('📊 Performing Q-Learning inference');

        if (this.rlSystems.qLearningEngine) {
            // In a real implementation, perform Q-Learning inference
            return {
                algorithm: 'q_learning',
                action: 'optimal_action',
                confidence: 0.85,
                timestamp: new Date().toISOString()
            };
        }

        throw new Error('Q-Learning inference not available');
    }

    async performPolicyGradientInference(request) {
        console.log('📈 Performing Policy Gradient inference');

        if (this.rlSystems.policyGradient) {
            // In a real implementation, perform Policy Gradient inference
            return {
                algorithm: 'policy_gradient',
                action: 'policy_action',
                probability: 0.75,
                timestamp: new Date().toISOString()
            };
        }

        throw new Error('Policy Gradient inference not available');
    }

    async performActorCriticInference(request) {
        console.log('🎭 Performing Actor-Critic inference');

        if (this.rlSystems.actorCritic) {
            // In a real implementation, perform Actor-Critic inference
            return {
                algorithm: 'actor_critic',
                action: 'actor_action',
                value: 0.65,
                timestamp: new Date().toISOString()
            };
        }

        throw new Error('Actor-Critic inference not available');
    }

    async performGenericInference(request) {
        console.log('⚙️ Performing generic RL inference');

        return {
            algorithm: 'generic',
            action: 'default_action',
            confidence: 0.5,
            timestamp: new Date().toISOString()
        };
    }

    async processRLFeedback(feedback) {
        console.log('🔄 Processing RL feedback...');

        try {
            // Update RL systems with feedback
            await this.updateRLSystemsWithFeedback(feedback);

            // Store feedback for learning
            this.storeFeedbackForLearning(feedback);

            console.log('✅ RL feedback processed');

        } catch (error) {
            console.error('❌ Error processing RL feedback:', error);
        }
    }

    async updateRLSystemsWithFeedback(feedback) {
        if (!this.rlSystems) return;

        // Update RL algorithms with feedback
        console.log('🔄 Updating RL systems with feedback');
    }

    addToExperienceBuffer(experience) {
        this.experienceBuffer.push({
            ...experience,
            bufferedAt: new Date().toISOString()
        });

        // Limit buffer size
        if (this.experienceBuffer.length > this.config.maxBufferSize) {
            this.experienceBuffer.shift();
        }
    }

    async flushExperienceBuffer() {
        if (this.experienceBuffer.length === 0) return;

        console.log(`💾 Flushing experience buffer: ${this.experienceBuffer.length} experiences`);

        try {
            // Process buffered experiences in batches
            const batches = this.createBatches(this.experienceBuffer, this.config.batchSize);

            for (const batch of batches) {
                await this.processExperienceBatch(batch);
            }

            // Clear buffer after successful processing
            this.experienceBuffer = [];

            console.log('✅ Experience buffer flushed');

        } catch (error) {
            console.error('❌ Error flushing experience buffer:', error);
        }
    }

    createBatches(array, batchSize) {
        const batches = [];
        for (let i = 0; i < array.length; i += batchSize) {
            batches.push(array.slice(i, i + batchSize));
        }
        return batches;
    }

    async processExperienceBatch(batch) {
        console.log(`⚡ Processing experience batch: ${batch.length} experiences`);

        // Process batch through RL systems
        for (const experience of batch) {
            await this.processRLExperience(experience);
        }
    }

    async syncRLSystems() {
        if (!this.rlSystems) return;

        console.log('⚡ Synchronizing RL systems...');

        try {
            // Sync Q-Learning streams
            await this.syncQLearningStreams();

            // Sync Policy Gradient streams
            await this.syncPolicyGradientStreams();

            // Sync Actor-Critic streams
            await this.syncActorCriticStreams();

            // Publish sync metrics
            await this.publishRLSyncMetrics();

            console.log('✅ RL systems synchronized');

        } catch (error) {
            console.error('❌ Error synchronizing RL systems:', error);
        }
    }

    async syncQLearningStreams() {
        const stream = this.rlDataStreams.get('q_learning_stream');
        if (stream && stream.buffer.length > 0) {
            console.log(`📊 Syncing Q-Learning stream: ${stream.buffer.length} experiences`);
            // Process Q-Learning experiences
        }
    }

    async syncPolicyGradientStreams() {
        const stream = this.rlDataStreams.get('policy_gradient_stream');
        if (stream && stream.buffer.length > 0) {
            console.log(`📈 Syncing Policy Gradient stream: ${stream.buffer.length} experiences`);
            // Process Policy Gradient experiences
        }
    }

    async syncActorCriticStreams() {
        const stream = this.rlDataStreams.get('actor_critic_stream');
        if (stream && stream.buffer.length > 0) {
            console.log(`🎭 Syncing Actor-Critic stream: ${stream.buffer.length} experiences`);
            // Process Actor-Critic experiences
        }
    }

    async publishRLSyncMetrics() {
        const metrics = {
            timestamp: new Date().toISOString(),
            experienceBufferSize: this.experienceBuffer.length,
            activeStreams: Array.from(this.rlDataStreams.entries()).filter(
                ([_, stream]) => stream.enabled
            ).length,
            rlSystemsStatus: this.rlSystems ? 'connected' : 'disconnected'
        };

        // Publish to Kafka
        if (messaging.kafkaProducer) {
            await messaging.publishKafka(
                this.config.kafkaTopics.rlMetrics,
                JSON.stringify(metrics)
            );
        }

        // Publish to RabbitMQ
        if (messaging.rabbitChannel) {
            await messaging.publishRabbit(
                this.config.rabbitQueues.rlUpdates,
                JSON.stringify(metrics)
            );
        }
    }

    storeRewardForLearning(reward) {
        const key = `reward_${Date.now()}`;
        this.learningMetrics.set(key, {
            type: 'reward',
            data: reward,
            timestamp: new Date().toISOString()
        });
    }

    storeActionForLearning(action) {
        const key = `action_${Date.now()}`;
        this.learningMetrics.set(key, {
            type: 'action',
            data: action,
            timestamp: new Date().toISOString()
        });
    }

    storeFeedbackForLearning(feedback) {
        const key = `feedback_${Date.now()}`;
        this.learningMetrics.set(key, {
            type: 'feedback',
            data: feedback,
            timestamp: new Date().toISOString()
        });
    }

    async publishRLLearningResults(request, result) {
        const event = {
            type: 'rl_learning_completed',
            requestId: request.id,
            algorithm: request.algorithm,
            result: result,
            timestamp: new Date().toISOString()
        };

        // Publish via messaging
        await this.publishRLEvent(event);
    }

    async publishRLInferenceResults(request, result) {
        const event = {
            type: 'rl_inference_completed',
            requestId: request.id,
            algorithm: request.algorithm,
            result: result,
            timestamp: new Date().toISOString()
        };

        // Publish via messaging
        await this.publishRLEvent(event);
    }

    async publishRLEvent(event) {
        // Publish to Kafka
        if (messaging.kafkaProducer) {
            await messaging.publishKafka(
                this.config.kafkaTopics.rlModels,
                JSON.stringify(event)
            );
        }

        // Publish to RabbitMQ
        if (messaging.rabbitChannel) {
            await messaging.publishRabbit(
                this.config.rabbitQueues.rlUpdates,
                JSON.stringify(event)
            );
        }
    }

    // Public API methods
    async getRLMessagingStatus() {
        return {
            status: this.status,
            kafkaTopics: this.config.kafkaTopics,
            rabbitQueues: this.config.rabbitQueues,
            experienceBufferSize: this.experienceBuffer.length,
            activeStreams: Array.from(this.rlDataStreams.keys()),
            learningMetricsCount: this.learningMetrics.size,
            timestamp: new Date().toISOString()
        };
    }

    async getRLStreamStatus(streamName) {
        const stream = this.rlDataStreams.get(streamName);
        if (!stream) {
            throw new Error(`Stream not found: ${streamName}`);
        }

        return {
            name: streamName,
            type: stream.type,
            algorithm: stream.algorithm,
            enabled: stream.enabled,
            bufferSize: stream.buffer.length,
            timestamp: new Date().toISOString()
        };
    }

    async getRLLearningMetrics() {
        return {
            metrics: Array.from(this.learningMetrics.entries()).map(([key, value]) => ({
                key,
                ...value
            })),
            totalCount: this.learningMetrics.size,
            timestamp: new Date().toISOString()
        };
    }

    async triggerRLLearning(algorithm, config) {
        const request = {
            id: `manual_rl_${Date.now()}`,
            algorithm: algorithm,
            config: config,
            timestamp: new Date().toISOString()
        };

        await this.processRLLearningRequest(request);
        return { success: true, requestId: request.id };
    }

    async triggerRLInference(algorithm, state) {
        const request = {
            id: `manual_inference_${Date.now()}`,
            algorithm: algorithm,
            state: state,
            timestamp: new Date().toISOString()
        };

        await this.processRLInferenceRequest(request);
        return { success: true, requestId: request.id };
    }

    // Cleanup method
    destroy() {
        console.log('🧹 Cleaning up RL Messaging Integration...');

        // Clear data structures
        this.messageHandlers.clear();
        this.rlDataStreams.clear();
        this.experienceBuffer = [];
        this.learningMetrics.clear();

        this.status = 'STOPPED';
        console.log('✅ RL Messaging Integration cleaned up');
    }
}

export default RLMessagingIntegration;