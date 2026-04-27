import Anthropic from '@anthropic-ai/sdk';
import { MemoryDatabase, Observation } from './database.js';

export class SDKAgent {
  private client: Anthropic;
  private db: MemoryDatabase;
  private processing: boolean = false;

  constructor(db: MemoryDatabase, apiKey?: string) {
    this.db = db;
    this.client = new Anthropic({
      apiKey: apiKey || process.env.ANTHROPIC_API_KEY,
    });
  }

  /**
   * Start the compression queue processor
   */
  async start() {
    if (this.processing) {
      console.log('[SDK Agent] Already processing');
      return;
    }

    this.processing = true;
    console.log('[SDK Agent] Starting compression queue processor');

    while (this.processing) {
      try {
        await this.processQueue();
        // Wait 1 second between checks
        await this.sleep(1000);
      } catch (error) {
        console.error('[SDK Agent] Error in queue processor:', error);
        await this.sleep(5000); // Wait longer on error
      }
    }
  }

  /**
   * Stop the compression queue processor
   */
  stop() {
    this.processing = false;
    console.log('[SDK Agent] Stopping compression queue processor');
  }

  /**
   * Process pending observations
   */
  private async processQueue() {
    // Get next pending observation
    const observations = this.db.getPendingObservations(1);
    if (observations.length === 0) {
      return; // Nothing to process
    }

    const observation = observations[0];
    console.log(`[SDK Agent] Processing observation #${observation.id} (${observation.tool_name})`);

    try {
      // Generate compression prompt
      const prompt = this.generateCompressionPrompt(observation);

      // Call Claude API (using Haiku 4.5 for cost optimization - 90% cheaper)
      const response = await this.client.messages.create({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 300,
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ]
      });

      // Extract compressed observation from response
      const content = response.content[0];
      if (content.type === 'text') {
        const compressed = this.extractCompressedObservation(content.text);

        // Update database
        this.db.updateObservationCompression(observation.id, compressed);

        console.log(`[SDK Agent] Compressed observation #${observation.id}: ${compressed.substring(0, 100)}...`);
      }
    } catch (error) {
      console.error(`[SDK Agent] Failed to compress observation #${observation.id}:`, error);
      // Mark as processed with error marker to avoid infinite retries
      this.db.updateObservationCompression(observation.id, '[Compression failed]');
    }
  }

  /**
   * Generate compression prompt for an observation
   */
  private generateCompressionPrompt(observation: Observation): string {
    const input = observation.tool_input || '[No input]';
    const response = observation.tool_response || '[No response]';

    return `You are observing a tool execution. Compress this observation into 2-3 sentences focusing on what was learned, discovered, or changed. Be concise but preserve important technical details.

Tool: ${observation.tool_name}
Input: ${input.substring(0, 1000)}${input.length > 1000 ? '... [truncated]' : ''}
Response: ${response.substring(0, 2000)}${response.length > 2000 ? '... [truncated]' : ''}

Provide output in XML format:
<compressed_observation>
[Your 2-3 sentence summary]
</compressed_observation>`;
  }

  /**
   * Extract compressed observation from XML response
   */
  private extractCompressedObservation(text: string): string {
    const match = text.match(/<compressed_observation>([\s\S]*?)<\/compressed_observation>/);
    if (match && match[1]) {
      return match[1].trim();
    }

    // Fallback: use the entire text
    return text.trim();
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
