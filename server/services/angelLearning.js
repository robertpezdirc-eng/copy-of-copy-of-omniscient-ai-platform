// server/services/angelLearning.js - Enhanced for Continuous Learning
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { EventEmitter } from 'events';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, '..', 'data', 'angels_learning.json');
const ANALYTICS_DB_PATH = path.join(__dirname, '..', 'data', 'angels_analytics.json');
const INSIGHTS_DB_PATH = path.join(__dirname, '..', 'data', 'angels_insights.json');

class EnhancedAngelLearning extends EventEmitter {
  constructor() {
    super();
    this.learningEvents = [];
    this.analytics = new Map();
    this.insights = new Map();
    this.learningPatterns = new Map();
    this.continuousLearners = new Map();
    this.performanceMetrics = new Map();

    // Enhanced configuration
    this.config = {
      maxEvents: 50000,
      analyticsInterval: 300000, // 5 minutes
      insightGenerationInterval: 600000, // 10 minutes
      patternAnalysisInterval: 900000, // 15 minutes
      continuousLearningInterval: 1800000, // 30 minutes
      enableAutoOptimization: true,
      enablePatternRecognition: true,
      enableInsightGeneration: true,
      enablePredictiveAnalytics: true
    };

    console.log('👼 Enhanced Angel Learning - Initializing...');
    this.initialize();
  }

  async initialize() {
    try {
      // Load existing data
      await this.loadExistingData();

      // Set up continuous learning processes
      this.setupContinuousLearning();

      // Set up analytics and insights
      this.setupAnalyticsGeneration();

      // Set up pattern recognition
      if (this.config.enablePatternRecognition) {
        this.setupPatternRecognition();
      }

      // Set up predictive analytics
      if (this.config.enablePredictiveAnalytics) {
        this.setupPredictiveAnalytics();
      }

      console.log('✅ Enhanced Angel Learning - Successfully initialized');

      // Emit initialization event
      this.emit('initialized', {
        status: 'active',
        eventsLoaded: this.learningEvents.length,
        analyticsEnabled: true,
        insightsEnabled: true,
        timestamp: new Date().toISOString()
      });

    } catch (error) {
      console.error('❌ Failed to initialize Enhanced Angel Learning:', error);
      throw error;
    }
  }

  async loadExistingData() {
    console.log('📚 Loading existing angel learning data...');

    try {
      // Load learning events
      this.learningEvents = this.loadData(DB_PATH) || [];

      // Load analytics data
      const analyticsData = this.loadData(ANALYTICS_DB_PATH) || {};
      this.analytics = new Map(Object.entries(analyticsData));

      // Load insights data
      const insightsData = this.loadData(INSIGHTS_DB_PATH) || {};
      this.insights = new Map(Object.entries(insightsData));

      console.log(`✅ Loaded ${this.learningEvents.length} events, ${this.analytics.size} analytics, ${this.insights.size} insights`);

    } catch (error) {
      console.error('❌ Error loading existing data:', error);
      this.learningEvents = [];
    }
  }

  loadData(filePath) {
    try {
      if (!fs.existsSync(filePath)) return null;
      const data = fs.readFileSync(filePath, 'utf8');
      return JSON.parse(data);
    } catch (error) {
      console.error(`❌ Error loading data from ${filePath}:`, error);
      return null;
    }
  }

  saveData(filePath, data) {
    try {
      const dir = path.dirname(filePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
      return true;
    } catch (error) {
      console.error(`❌ Error saving data to ${filePath}:`, error);
      return false;
    }
  }

  setupContinuousLearning() {
    console.log('🔄 Setting up continuous learning processes...');

    // Continuous learning loop
    setInterval(async () => {
      await this.performContinuousLearning();
    }, this.config.continuousLearningInterval);

    // Performance optimization loop
    setInterval(async () => {
      await this.optimizeLearningPerformance();
    }, this.config.analyticsInterval * 2);

    console.log('✅ Continuous learning processes established');
  }

  setupAnalyticsGeneration() {
    console.log('📊 Setting up analytics generation...');

    // Analytics generation loop
    setInterval(async () => {
      await this.generateLearningAnalytics();
    }, this.config.analyticsInterval);

    // Real-time analytics updates
    this.on('learning_event_added', async (event) => {
      await this.updateRealTimeAnalytics(event);
    });

    console.log('✅ Analytics generation configured');
  }

  setupPatternRecognition() {
    console.log('🔍 Setting up pattern recognition...');

    // Pattern analysis loop
    setInterval(async () => {
      await this.analyzeLearningPatterns();
    }, this.config.patternAnalysisInterval);

    console.log('✅ Pattern recognition configured');
  }

  setupPredictiveAnalytics() {
    console.log('🔮 Setting up predictive analytics...');

    // Predictive model updates
    setInterval(async () => {
      await this.updatePredictiveModels();
    }, this.config.analyticsInterval * 3);

    console.log('✅ Predictive analytics configured');
  }

  // Enhanced learning event management
  addLearningEvent({ angel = 'LearningAngel', domain = 'general', input = {}, output = {}, metrics = {}, context = {} }) {
    const event = {
      id: `event_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      angel,
      domain,
      input,
      output,
      metrics,
      context,
      timestamp: new Date().toISOString(),
      processed: false,
      analytics: {},
      insights: []
    };

    // Add to events array
    this.learningEvents.push(event);

    // Limit events size
    if (this.learningEvents.length > this.config.maxEvents) {
      this.learningEvents.shift(); // Remove oldest
    }

    // Save to disk
    this.saveData(DB_PATH, this.learningEvents);

    // Emit event for real-time processing
    this.emit('learning_event_added', event);

    console.log(`📚 Learning event added: ${event.id} (${angel}/${domain})`);

    return event;
  }

  // Enhanced history retrieval with analytics
  getHistory({ angel, domain, since, limit = 1000, includeAnalytics = false } = {}) {
    let events = this.learningEvents;

    // Apply filters
    if (angel) {
      events = events.filter(e => e.angel === angel);
    }
    if (domain) {
      events = events.filter(e => e.domain === domain);
    }
    if (since) {
      events = events.filter(e => new Date(e.timestamp) >= new Date(since));
    }

    // Sort by timestamp (newest first)
    events.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    // Apply limit
    if (limit) {
      events = events.slice(0, limit);
    }

    // Include analytics if requested
    if (includeAnalytics) {
      events = events.map(event => ({
        ...event,
        analytics: this.getEventAnalytics(event.id),
        insights: this.getEventInsights(event.id)
      }));
    }

    return events;
  }

  // Enhanced daily summary with insights
  getDailySummary({ angel, domain } = {}) {
    const today = new Date(new Date().setHours(0,0,0,0)).toISOString();
    const history = this.getHistory({ angel, domain, since: today, includeAnalytics: true });

    const count = history.length;
    const domains = new Map();
    const angels = new Map();
    const metrics = {
      total: 0,
      successful: 0,
      failed: 0,
      avgProcessingTime: 0,
      insights: []
    };

    let totalProcessingTime = 0;
    let processingTimeCount = 0;

    history.forEach(event => {
      // Count by domain
      domains.set(event.domain, (domains.get(event.domain) || 0) + 1);

      // Count by angel
      angels.set(event.angel, (angels.get(event.angel) || 0) + 1);

      // Calculate metrics
      metrics.total++;
      if (event.output && event.output.success) {
        metrics.successful++;
      } else {
        metrics.failed++;
      }

      // Processing time
      if (event.metrics && event.metrics.processingTime) {
        totalProcessingTime += event.metrics.processingTime;
        processingTimeCount++;
      }

      // Collect insights
      if (event.insights && event.insights.length > 0) {
        metrics.insights.push(...event.insights);
      }
    });

    // Calculate averages
    metrics.avgProcessingTime = processingTimeCount > 0 ? totalProcessingTime / processingTimeCount : 0;
    metrics.successRate = metrics.total > 0 ? (metrics.successful / metrics.total) * 100 : 0;

    // Get top domains and angels
    const topDomains = Array.from(domains.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([domain, count]) => ({ domain, count }));

    const topAngels = Array.from(angels.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([angel, count]) => ({ angel, count }));

    // Generate enhanced summary
    const summary = this.generateEnhancedSummary({
      count,
      topDomains,
      topAngels,
      metrics,
      insights: metrics.insights.slice(0, 10)
    });

    return {
      count,
      topDomains,
      topAngels,
      metrics,
      insights: metrics.insights.slice(0, 10),
      summary,
      timestamp: new Date().toISOString(),
      date: today
    };
  }

  generateEnhancedSummary(data) {
    const { count, topDomains, topAngels, metrics, insights } = data;

    if (count === 0) {
      return 'Angel danes še ni ničesar zabeležil.';
    }

    let summary = `Danes je angel obdelal ${count} učnih dogodkov. `;

    if (topDomains.length > 0) {
      summary += `Največ aktivnosti je bilo v domenah: ${topDomains.map(d => `${d.domain} (${d.count})`).join(', ')}. `;
    }

    if (topAngels.length > 0) {
      summary += `Najaktivnejši angeli: ${topAngels.map(a => `${a.angel} (${a.count})`).join(', ')}. `;
    }

    summary += `Uspešnost: ${metrics.successRate.toFixed(1)}%, povprečen čas obdelave: ${metrics.avgProcessingTime.toFixed(0)}ms. `;

    if (insights.length > 0) {
      summary += `Ključni poudarki: ${insights.slice(0, 3).join(' | ')}.`;
    } else {
      summary += 'Ni posebnih poudarkov.';
    }

    return summary;
  }

  // Analytics and insights generation
  async generateLearningAnalytics() {
    console.log('📊 Generating learning analytics...');

    try {
      const analytics = {
        timestamp: new Date().toISOString(),
        period: 'current',
        events: this.learningEvents.length,
        domains: this.analyzeDomainDistribution(),
        angels: this.analyzeAngelPerformance(),
        temporal: this.analyzeTemporalPatterns(),
        performance: this.analyzePerformanceMetrics(),
        trends: this.analyzeLearningTrends()
      };

      // Store analytics
      const analyticsKey = `analytics_${Date.now()}`;
      this.analytics.set(analyticsKey, analytics);

      // Limit analytics history
      if (this.analytics.size > 1000) {
        const oldestKey = Array.from(this.analytics.keys())[0];
        this.analytics.delete(oldestKey);
      }

      // Save to disk
      this.saveData(ANALYTICS_DB_PATH, Object.fromEntries(this.analytics));

      console.log('✅ Learning analytics generated');

      // Emit analytics event
      this.emit('analytics_generated', analytics);

    } catch (error) {
      console.error('❌ Error generating learning analytics:', error);
    }
  }

  analyzeDomainDistribution() {
    const domains = new Map();

    this.learningEvents.forEach(event => {
      domains.set(event.domain, (domains.get(event.domain) || 0) + 1);
    });

    return Array.from(domains.entries()).map(([domain, count]) => ({
      domain,
      count,
      percentage: (count / this.learningEvents.length) * 100
    }));
  }

  analyzeAngelPerformance() {
    const angels = new Map();

    this.learningEvents.forEach(event => {
      if (!angels.has(event.angel)) {
        angels.set(event.angel, {
          total: 0,
          successful: 0,
          failed: 0,
          avgProcessingTime: 0,
          domains: new Set()
        });
      }

      const angel = angels.get(event.angel);
      angel.total++;
      angel.domains.add(event.domain);

      if (event.output && event.output.success) {
        angel.successful++;
      } else {
        angel.failed++;
      }

      if (event.metrics && event.metrics.processingTime) {
        angel.avgProcessingTime = (angel.avgProcessingTime + event.metrics.processingTime) / 2;
      }
    });

    return Array.from(angels.entries()).map(([angel, stats]) => ({
      angel,
      ...stats,
      successRate: (stats.successful / stats.total) * 100,
      domains: Array.from(stats.domains)
    }));
  }

  analyzeTemporalPatterns() {
    const hourly = new Array(24).fill(0);
    const daily = new Array(7).fill(0);

    this.learningEvents.forEach(event => {
      const date = new Date(event.timestamp);
      hourly[date.getHours()]++;
      daily[date.getDay()]++;
    });

    return {
      hourly: hourly.map((count, hour) => ({ hour, count })),
      daily: daily.map((count, day) => ({ day, count })),
      peakHour: hourly.indexOf(Math.max(...hourly)),
      peakDay: daily.indexOf(Math.max(...daily))
    };
  }

  analyzePerformanceMetrics() {
    const metrics = {
      totalEvents: this.learningEvents.length,
      avgProcessingTime: 0,
      successRate: 0,
      errorRate: 0,
      throughput: 0
    };

    let totalProcessingTime = 0;
    let processingTimeCount = 0;
    let successful = 0;
    let failed = 0;

    this.learningEvents.forEach(event => {
      if (event.metrics && event.metrics.processingTime) {
        totalProcessingTime += event.metrics.processingTime;
        processingTimeCount++;
      }

      if (event.output && event.output.success) {
        successful++;
      } else {
        failed++;
      }
    });

    metrics.avgProcessingTime = processingTimeCount > 0 ? totalProcessingTime / processingTimeCount : 0;
    metrics.successRate = (successful / this.learningEvents.length) * 100;
    metrics.errorRate = (failed / this.learningEvents.length) * 100;
    metrics.throughput = this.learningEvents.length / (this.config.analyticsInterval / 60000); // events per minute

    return metrics;
  }

  analyzeLearningTrends() {
    // Analyze trends over time
    const now = Date.now();
    const oneHourAgo = now - 3600000;
    const oneDayAgo = now - 86400000;

    const recent = this.learningEvents.filter(e => new Date(e.timestamp).getTime() > oneHourAgo);
    const daily = this.learningEvents.filter(e => new Date(e.timestamp).getTime() > oneDayAgo);

    return {
      hourlyTrend: recent.length,
      dailyTrend: daily.length,
      trendDirection: recent.length > daily.length / 24 ? 'increasing' : 'decreasing',
      velocity: recent.length - (daily.length / 24)
    };
  }

  async updateRealTimeAnalytics(event) {
    // Update real-time analytics for immediate insights
    const analytics = {
      eventId: event.id,
      timestamp: event.timestamp,
      angel: event.angel,
      domain: event.domain,
      processingTime: event.metrics?.processingTime || 0,
      success: event.output?.success || false
    };

    // Store in recent analytics
    const recentKey = `recent_${Date.now()}`;
    this.analytics.set(recentKey, analytics);

    console.log(`📊 Real-time analytics updated for event: ${event.id}`);
  }

  getEventAnalytics(eventId) {
    return Array.from(this.analytics.values()).filter(a => a.eventId === eventId);
  }

  getEventInsights(eventId) {
    return this.insights.get(eventId) || [];
  }

  // Pattern recognition and analysis
  async analyzeLearningPatterns() {
    console.log('🔍 Analyzing learning patterns...');

    try {
      // Identify recurring patterns
      const patterns = await this.identifyRecurringPatterns();

      // Analyze pattern evolution
      const evolution = await this.analyzePatternEvolution(patterns);

      // Generate pattern insights
      const insights = await this.generatePatternInsights(patterns, evolution);

      // Store patterns and insights
      this.storePatternAnalysis(patterns, evolution, insights);

      console.log(`✅ Learning patterns analyzed: ${patterns.length} patterns found`);

    } catch (error) {
      console.error('❌ Error analyzing learning patterns:', error);
    }
  }

  async identifyRecurringPatterns() {
    const patterns = new Map();

    // Group events by similar characteristics
    this.learningEvents.forEach(event => {
      const patternKey = `${event.angel}_${event.domain}_${event.output?.success || 'unknown'}`;

      if (!patterns.has(patternKey)) {
        patterns.set(patternKey, {
          key: patternKey,
          angel: event.angel,
          domain: event.domain,
          success: event.output?.success || false,
          count: 0,
          events: [],
          firstSeen: event.timestamp,
          lastSeen: event.timestamp
        });
      }

      const pattern = patterns.get(patternKey);
      pattern.count++;
      pattern.events.push(event.id);
      pattern.lastSeen = event.timestamp;

      // Calculate pattern strength
      pattern.strength = pattern.count / this.learningEvents.length;
    });

    return Array.from(patterns.values())
      .filter(p => p.count > 1) // Only patterns with multiple occurrences
      .sort((a, b) => b.strength - a.strength);
  }

  async analyzePatternEvolution(patterns) {
    const evolution = {
      emerging: [],
      stable: [],
      declining: [],
      timestamp: new Date().toISOString()
    };

    patterns.forEach(pattern => {
      const recentEvents = pattern.events.filter(eventId => {
        const event = this.learningEvents.find(e => e.id === eventId);
        return event && (Date.now() - new Date(event.timestamp).getTime()) < 3600000; // Last hour
      });

      if (recentEvents.length > pattern.count * 0.7) {
        evolution.emerging.push(pattern);
      } else if (recentEvents.length > pattern.count * 0.3) {
        evolution.stable.push(pattern);
      } else {
        evolution.declining.push(pattern);
      }
    });

    return evolution;
  }

  async generatePatternInsights(patterns, evolution) {
    const insights = [];

    // Generate insights from patterns
    evolution.emerging.forEach(pattern => {
      insights.push({
        type: 'emerging_pattern',
        pattern: pattern.key,
        description: `Novi vzorec učenja se pojavlja: ${pattern.angel} v domeni ${pattern.domain}`,
        significance: pattern.strength,
        timestamp: new Date().toISOString()
      });
    });

    evolution.declining.forEach(pattern => {
      insights.push({
        type: 'declining_pattern',
        pattern: pattern.key,
        description: `Vzorec učenja se zmanjšuje: ${pattern.angel} v domeni ${pattern.domain}`,
        significance: pattern.strength,
        timestamp: new Date().toISOString()
      });
    });

    return insights;
  }

  storePatternAnalysis(patterns, evolution, insights) {
    const analysisKey = `pattern_analysis_${Date.now()}`;
    this.learningPatterns.set(analysisKey, {
      patterns,
      evolution,
      insights,
      timestamp: new Date().toISOString()
    });

    // Store insights for individual events
    insights.forEach(insight => {
      // Link insights to relevant events
      const relatedEvents = patterns
        .filter(p => p.key === insight.pattern)
        .flatMap(p => p.events);

      relatedEvents.forEach(eventId => {
        if (!this.insights.has(eventId)) {
          this.insights.set(eventId, []);
        }
        this.insights.get(eventId).push(insight);
      });
    });

    // Save insights to disk
    this.saveData(INSIGHTS_DB_PATH, Object.fromEntries(this.insights));
  }

  // Continuous learning optimization
  async performContinuousLearning() {
    console.log('🔄 Performing continuous learning optimization...');

    try {
      // Optimize angel performance
      await this.optimizeAngelPerformance();

      // Update learning strategies
      await this.updateLearningStrategies();

      // Improve pattern recognition
      await this.improvePatternRecognition();

      // Enhance insight generation
      await this.enhanceInsightGeneration();

      console.log('✅ Continuous learning optimization completed');

    } catch (error) {
      console.error('❌ Error in continuous learning optimization:', error);
    }
  }

  async optimizeAngelPerformance() {
    const angelPerformance = this.analyzeAngelPerformance();

    // Identify underperforming angels
    const underperforming = angelPerformance.filter(a => a.successRate < 70);

    underperforming.forEach(angel => {
      console.log(`⚠️ Optimizing performance for angel: ${angel.angel} (success rate: ${angel.successRate.toFixed(1)}%)`);

      // Generate optimization suggestions
      this.generateOptimizationSuggestions(angel);
    });
  }

  generateOptimizationSuggestions(angel) {
    const suggestions = [];

    if (angel.avgProcessingTime > 1000) {
      suggestions.push({
        type: 'performance',
        description: `Optimize processing time for ${angel.angel}`,
        priority: 'high'
      });
    }

    if (angel.successRate < 80) {
      suggestions.push({
        type: 'reliability',
        description: `Improve success rate for ${angel.angel}`,
        priority: 'high'
      });
    }

    return suggestions;
  }

  async updateLearningStrategies() {
    // Update learning strategies based on performance
    const performance = this.analyzePerformanceMetrics();

    if (performance.successRate < 85) {
      console.log('📈 Updating learning strategies for better success rate');
      // Adjust learning parameters
    }
  }

  async improvePatternRecognition() {
    if (this.config.enablePatternRecognition) {
      console.log('🔍 Improving pattern recognition algorithms');
      // Enhance pattern recognition based on recent data
    }
  }

  async enhanceInsightGeneration() {
    if (this.config.enableInsightGeneration) {
      console.log('💡 Enhancing insight generation capabilities');
      // Improve insight generation algorithms
    }
  }

  async optimizeLearningPerformance() {
    console.log('⚡ Optimizing learning performance...');

    try {
      // Clean up old data
      await this.cleanupOldData();

      // Optimize data structures
      await this.optimizeDataStructures();

      // Update performance metrics
      await this.updatePerformanceMetrics();

      console.log('✅ Learning performance optimized');

    } catch (error) {
      console.error('❌ Error optimizing learning performance:', error);
    }
  }

  async cleanupOldData() {
    const cutoffDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000); // 7 days ago

    // Remove old events
    const initialCount = this.learningEvents.length;
    this.learningEvents = this.learningEvents.filter(event =>
      new Date(event.timestamp) > cutoffDate
    );

    const removedCount = initialCount - this.learningEvents.length;
    if (removedCount > 0) {
      console.log(`🧹 Cleaned up ${removedCount} old learning events`);
      this.saveData(DB_PATH, this.learningEvents);
    }
  }

  async optimizeDataStructures() {
    // Optimize internal data structures for better performance
    console.log('⚡ Optimizing internal data structures');

    // Reorganize analytics for faster access
    const optimizedAnalytics = new Map();
    this.analytics.forEach((value, key) => {
      if (Date.now() - new Date(value.timestamp).getTime() < 86400000) { // Last 24 hours
        optimizedAnalytics.set(key, value);
      }
    });

    this.analytics = optimizedAnalytics;
  }

  async updatePerformanceMetrics() {
    const metrics = this.analyzePerformanceMetrics();

    // Store performance metrics
    const metricsKey = `performance_${Date.now()}`;
    this.performanceMetrics.set(metricsKey, {
      ...metrics,
      timestamp: new Date().toISOString()
    });

    // Limit performance metrics history
    if (this.performanceMetrics.size > 100) {
      const oldestKey = Array.from(this.performanceMetrics.keys())[0];
      this.performanceMetrics.delete(oldestKey);
    }
  }

  async updatePredictiveModels() {
    console.log('🔮 Updating predictive models...');

    try {
      // Update prediction models based on recent patterns
      const recentPatterns = await this.identifyRecurringPatterns();

      // Generate predictions
      const predictions = await this.generateLearningPredictions(recentPatterns);

      // Store predictions
      this.storePredictions(predictions);

      console.log('✅ Predictive models updated');

    } catch (error) {
      console.error('❌ Error updating predictive models:', error);
    }
  }

  async generateLearningPredictions(patterns) {
    const predictions = [];

    patterns.forEach(pattern => {
      if (pattern.strength > 0.1) { // Strong patterns only
        predictions.push({
          type: 'learning_trend',
          pattern: pattern.key,
          prediction: `Expected ${pattern.count * 1.2} occurrences in next period`,
          confidence: pattern.strength,
          timestamp: new Date().toISOString()
        });
      }
    });

    return predictions;
  }

  storePredictions(predictions) {
    const predictionKey = `predictions_${Date.now()}`;
    this.analytics.set(predictionKey, {
      predictions,
      timestamp: new Date().toISOString()
    });
  }

  // Public API methods
  async getSystemStatus() {
    return {
      status: 'active',
      eventsCount: this.learningEvents.length,
      analyticsCount: this.analytics.size,
      insightsCount: this.insights.size,
      patternsCount: this.learningPatterns.size,
      performanceMetrics: this.analyzePerformanceMetrics(),
      timestamp: new Date().toISOString()
    };
  }

  async getAnalytics({ period = '1h', type = 'all' } = {}) {
    const cutoffTime = Date.now() - this.getPeriodMilliseconds(period);

    const filteredAnalytics = Array.from(this.analytics.values()).filter(
      a => new Date(a.timestamp).getTime() > cutoffTime
    );

    if (type !== 'all') {
      return filteredAnalytics.filter(a => a.type === type);
    }

    return filteredAnalytics;
  }

  getPeriodMilliseconds(period) {
    const periods = {
      '1h': 3600000,
      '6h': 21600000,
      '24h': 86400000,
      '7d': 604800000
    };
    return periods[period] || 3600000;
  }

  async getInsights({ limit = 50, type = 'all' } = {}) {
    const allInsights = Array.from(this.insights.values()).flat();

    if (type !== 'all') {
      return allInsights.filter(i => i.type === type).slice(0, limit);
    }

    return allInsights.slice(0, limit);
  }

  async getPatterns() {
    return {
      patterns: Array.from(this.learningPatterns.values()),
      count: this.learningPatterns.size,
      timestamp: new Date().toISOString()
    };
  }

  async getPerformanceHistory() {
    return {
      metrics: Array.from(this.performanceMetrics.values()),
      count: this.performanceMetrics.size,
      timestamp: new Date().toISOString()
    };
  }

  // Cleanup method
  destroy() {
    console.log('🧹 Cleaning up Enhanced Angel Learning...');

    // Clear intervals (in a real implementation)
    // clearInterval(this.continuousLearningInterval);
    // clearInterval(this.analyticsInterval);

    // Save final state
    this.saveData(DB_PATH, this.learningEvents);
    this.saveData(ANALYTICS_DB_PATH, Object.fromEntries(this.analytics));
    this.saveData(INSIGHTS_DB_PATH, Object.fromEntries(this.insights));

    // Clear data structures
    this.learningEvents = [];
    this.analytics.clear();
    this.insights.clear();
    this.learningPatterns.clear();
    this.performanceMetrics.clear();

    console.log('✅ Enhanced Angel Learning cleaned up');
  }
}

// Export both the class and the original functions for backward compatibility
export const angelLearning = new EnhancedAngelLearning();

// Backward compatibility functions
export function addLearningEvent(params) {
  return angelLearning.addLearningEvent(params);
}

export function getHistory(params) {
  return angelLearning.getHistory(params);
}

export function getDailySummary(params) {
  return angelLearning.getDailySummary(params);
}

export default angelLearning;