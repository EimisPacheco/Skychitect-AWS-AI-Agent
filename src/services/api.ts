/**
 * API Service for Skyrchitect AI Backend
 * Connects React frontend to FastAPI backend with Claude Sonnet 4
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ArchitectureRequirement {
  title: string;
  description: string;
  requirements: string[];
  provider: 'aws' | 'azure' | 'gcp';
  optimization_goal: 'cost' | 'performance' | 'balanced';
  budget?: number;
  expected_users?: number;
}

export interface ComponentOptimizationRequest {
  provider: 'aws' | 'azure' | 'gcp';
  components: Array<{
    name: string;
    category: string;
    cost: number;
  }>;
  current_cost: number;
  optimization_goal: 'cost' | 'performance' | 'balanced';
}

export interface DiagramAnalysisRequest {
  provider: 'aws' | 'azure' | 'gcp';
  nodes: string[];
  edges: string[];
  requirements?: string;
}

export interface AgentResponse {
  success: boolean;
  message: string;
  data: any;
  reasoning: string;
}

export interface HealthCheck {
  status: string;
  version: string;
  agent_ready: boolean;
  bedrock_connected: boolean;
  model_id: string;
}

class SkyrchitectAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  /**
   * Check API health status
   */
  async checkHealth(): Promise<HealthCheck> {
    const response = await fetch(`${this.baseURL}/`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Generate cloud architecture based on requirements
   */
  async generateArchitecture(req: ArchitectureRequirement): Promise<AgentResponse> {
    console.log('📤 Sending request to backend:');
    console.log('   Title:', req.title);
    console.log('   Description:', req.description);
    console.log('   Description length:', req.description.length, 'characters');
    console.log('   Provider:', req.provider);
    console.log('   Requirements:', req.requirements.length > 0 ? req.requirements : '(none - optional)');
    if (req.budget) console.log('   Budget:', req.budget);
    if (req.expected_users) console.log('   Expected Users:', req.expected_users);

    const response = await fetch(`${this.baseURL}/api/architecture/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(req),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Architecture generation failed: ${error}`);
    }

    const result = await response.json();
    console.log('📥 Received response from backend:', {
      success: result.success,
      hasData: !!result.data,
      hasDiagram: !!result.data?.diagram
    });

    return result;
  }

  /**
   * Optimize existing architecture
   */
  async optimizeArchitecture(req: ComponentOptimizationRequest): Promise<AgentResponse> {
    const response = await fetch(`${this.baseURL}/api/architecture/optimize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(req),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Architecture optimization failed: ${error}`);
    }

    return response.json();
  }

  /**
   * Validate architecture design
   */
  async validateArchitecture(req: DiagramAnalysisRequest): Promise<AgentResponse> {
    const response = await fetch(`${this.baseURL}/api/architecture/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(req),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Architecture validation failed: ${error}`);
    }

    return response.json();
  }

  /**
   * Compare cloud service across providers
   */
  async compareCloudService(serviceName: string): Promise<AgentResponse> {
    const response = await fetch(
      `${this.baseURL}/api/cloud/compare/${encodeURIComponent(serviceName)}`
    );

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Service comparison failed: ${error}`);
    }

    return response.json();
  }

  /**
   * Chat with AI agent
   */
  async chat(question: string, context?: string): Promise<AgentResponse> {
    const response = await fetch(`${this.baseURL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question, context }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Chat failed: ${error}`);
    }

    return response.json();
  }

  /**
   * Generate Infrastructure as Code (Terraform or CloudFormation)
   */
  async generateCode(architecture: any, codeType: 'terraform' | 'cloudformation' = 'terraform'): Promise<AgentResponse> {
    const response = await fetch(`${this.baseURL}/api/code/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ architecture, code_type: codeType }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Code generation failed: ${error}`);
    }

    return response.json();
  }

  /**
   * Deploy architecture to cloud provider
   */
  async deployArchitecture(architecture: any, config: any): Promise<AgentResponse> {
    const response = await fetch(`${this.baseURL}/api/deploy`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ architecture, config }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Deployment failed: ${error}`);
    }

    return response.json();
  }

  /**
   * Analyze architecture diagram from uploaded image/PDF
   */
  async analyzeImage(file: File): Promise<AgentResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseURL}/api/architecture/analyze-image`, {
      method: 'POST',
      body: formData, // Note: Don't set Content-Type header, browser will set it with boundary
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Image analysis failed: ${error}`);
    }

    return response.json();
  }
}

// Export singleton instance
export const api = new SkyrchitectAPI();

// Export class for testing or custom instances
export default SkyrchitectAPI;
