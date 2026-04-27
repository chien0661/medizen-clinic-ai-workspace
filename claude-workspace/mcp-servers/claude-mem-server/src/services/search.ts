import { MemoryDatabase, Observation } from './database.js';

export interface SearchResult {
  id: number;
  title: string;
  timestamp: string;
  type: string;
  project: string | null;
}

export interface TimelineResult {
  observations: SearchResult[];
  anchor_index: number;
}

export class SearchService {
  private db: MemoryDatabase;

  constructor(db: MemoryDatabase) {
    this.db = db;
  }

  /**
   * Layer 1: Search - Get compact index of matching observations
   * Returns ~50-100 tokens per result
   */
  search(params: {
    query: string;
    limit?: number;
    project?: string;
    type?: string;
    order?: 'relevance' | 'chronological';
  }): SearchResult[] {
    const { query, limit = 20, project, type, order = 'relevance' } = params;

    const observations = this.db.searchObservations(query, project, type, limit);

    return observations.map(obs => ({
      id: obs.id,
      title: `${obs.tool_name} ${obs.tool_input?.substring(0, 50) || ''}`.trim(),
      timestamp: obs.created_at,
      type: obs.tool_name,
      project: obs.project_name
    }));
  }

  /**
   * Layer 2: Timeline - Get chronological context around specific observation
   * Returns ~200-300 tokens per observation
   */
  timeline(params: {
    anchor_id?: number;
    query?: string;
    before?: number;
    after?: number;
  }): TimelineResult {
    const { anchor_id, query, before = 5, after = 5 } = params;

    // If query provided, find best matching observation first
    let anchorId = anchor_id;
    if (query && !anchorId) {
      const results = this.search({ query, limit: 1 });
      if (results.length > 0) {
        anchorId = results[0].id;
      }
    }

    if (!anchorId) {
      return { observations: [], anchor_index: -1 };
    }

    // Get the anchor observation
    const anchor = this.db.getObservationById(anchorId);
    if (!anchor) {
      return { observations: [], anchor_index: -1 };
    }

    // Get observations from the same session around the anchor
    const allObservations = this.db.getObservationsBySession(anchor.session_id);

    // Find anchor index
    const anchorIndex = allObservations.findIndex(o => o.id === anchorId);
    if (anchorIndex === -1) {
      return { observations: [], anchor_index: -1 };
    }

    // Get observations before and after
    const startIndex = Math.max(0, anchorIndex - before);
    const endIndex = Math.min(allObservations.length, anchorIndex + after + 1);

    const contextObservations = allObservations.slice(startIndex, endIndex);

    return {
      observations: contextObservations.map(obs => ({
        id: obs.id,
        title: `${obs.tool_name} ${obs.tool_input?.substring(0, 50) || ''}`.trim(),
        timestamp: obs.created_at,
        type: obs.tool_name,
        project: obs.project_name
      })),
      anchor_index: anchorIndex - startIndex
    };
  }

  /**
   * Layer 3: Get Full Details - Fetch complete observation data
   * Returns ~500-1,000 tokens per observation
   */
  getObservations(params: {
    ids: number[];
  }): Observation[] {
    const { ids } = params;

    return ids
      .map(id => this.db.getObservationById(id))
      .filter((obs): obs is Observation => obs !== undefined);
  }
}
