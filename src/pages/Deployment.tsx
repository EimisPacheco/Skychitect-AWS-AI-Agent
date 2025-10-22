import React, { useState } from 'react';
import { useLocation, Navigate } from 'react-router-dom';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import DeploymentForm from '../components/deployment/DeploymentForm';
import Particles from '../components/ui/Particles';
import Card from '../components/ui/Card';
import { Architecture, DeploymentConfig } from '../types';
import { Loader, CheckCircle } from 'lucide-react';
import { api } from '../services/api';

const Deployment: React.FC = () => {
  const location = useLocation();
  const { architecture } = location.state as { architecture: Architecture } || {};

  const [isDeploying, setIsDeploying] = useState(false);
  const [deploymentComplete, setDeploymentComplete] = useState(false);
  const [deploymentLogs, setDeploymentLogs] = useState<string[]>([]);
  const [deploymentUrl, setDeploymentUrl] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const handleDeploy = async (config: DeploymentConfig) => {
    setIsDeploying(true);
    setDeploymentLogs([]);
    setError(null);

    try {
      console.log('🚀 Starting deployment...');
      setDeploymentLogs(prev => [...prev, '[INFO] Initializing deployment process...']);
      setDeploymentLogs(prev => [...prev, `[INFO] Deploying to ${config.provider.toUpperCase()} in ${config.region}...`]);

      // Call backend API for deployment
      const response = await api.deployArchitecture(architecture, config);

      if (response.success && response.data) {
        const { deployment_logs, endpoint } = response.data;

        // Show backend-generated logs progressively
        deployment_logs.forEach((log: string, index: number) => {
          setTimeout(() => {
            setDeploymentLogs(prev => [...prev, log]);

            if (index === deployment_logs.length - 1) {
              setDeploymentUrl(endpoint || `https://${config.provider}-app.example.com`);
              setIsDeploying(false);
              setDeploymentComplete(true);
              console.log('✅ Deployment completed successfully!');
            }
          }, (index + 1) * 500);
        });
      } else {
        throw new Error('Deployment failed');
      }
    } catch (err) {
      console.error('❌ Deployment error:', err);
      setError(err instanceof Error ? err.message : 'Deployment failed');
      setDeploymentLogs(prev => [...prev, `[ERROR] ${err instanceof Error ? err.message : 'Deployment failed'}`]);
      setIsDeploying(false);
    }
  };
  
  // Redirect if no architecture is provided
  if (!architecture) {
    return <Navigate to="/architecture" replace />;
  }

  return (
    <div className="min-h-screen text-white">
      <Particles />
      <Header />
      
      <main className="container mx-auto px-4 pt-24 pb-16">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-3xl md:text-4xl font-bold mb-8 text-center">
            Deploy Your Architecture
          </h1>
          
          {!isDeploying && !deploymentComplete ? (
            <DeploymentForm architecture={architecture} onDeploy={handleDeploy} />
          ) : (
            <Card className="p-8 max-w-3xl mx-auto">
              <div className="flex items-center justify-center mb-6">
                {isDeploying ? (
                  <div className="flex flex-col items-center">
                    <Loader className="w-12 h-12 text-blue-500 animate-spin mb-4" />
                    <h2 className="text-2xl font-bold">Deploying Architecture</h2>
                    <p className="text-gray-400 mt-2">This may take a few minutes...</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <CheckCircle className="w-16 h-16 text-green-500 mb-4" />
                    <h2 className="text-2xl font-bold">Deployment Complete!</h2>
                    <p className="text-gray-300 mt-2">
                      Your architecture has been successfully deployed to {architecture.provider.toUpperCase()}
                    </p>
                  </div>
                )}
              </div>
              
              <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm h-64 overflow-y-auto">
                {deploymentLogs.map((log, index) => (
                  <div key={index} className="py-1">
                    <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span>{' '}
                    <span 
                      className={
                        log.includes('error') || log.includes('Error') 
                          ? 'text-red-400' 
                          : log.includes('completed') || log.includes('success')
                            ? 'text-green-400'
                            : 'text-gray-300'
                      }
                    >
                      {log}
                    </span>
                  </div>
                ))}
                
                {isDeploying && (
                  <div className="py-1 flex items-center">
                    <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span>{' '}
                    <span className="text-blue-400 ml-1 flex items-center">
                      Processing
                      <span className="ml-1 inline-flex">
                        <span className="animate-pulse">.</span>
                        <span className="animate-pulse delay-100">.</span>
                        <span className="animate-pulse delay-200">.</span>
                      </span>
                    </span>
                  </div>
                )}
              </div>
              
              {deploymentComplete && (
                <div className="mt-6 bg-green-900/20 border border-green-500/30 rounded-lg p-4">
                  <h3 className="font-bold text-green-400 mb-2">Deployment Summary</h3>
                  <ul className="text-sm text-gray-300 space-y-2">
                    <li>
                      <span className="text-gray-500">Provider:</span> {architecture.provider.toUpperCase()}
                    </li>
                    <li>
                      <span className="text-gray-500">Components:</span> {architecture.components.length} resources
                    </li>
                    <li>
                      <span className="text-gray-500">Estimated Monthly Cost:</span> ${
                        architecture.components.reduce((sum, comp) => sum + comp.cost, 0).toFixed(2)
                      }
                    </li>
                    <li>
                      <span className="text-gray-500">Deployment Status:</span> <span className="text-green-400">Successful</span>
                    </li>
                    <li>
                      <span className="text-gray-500">Access URL:</span> <a href={deploymentUrl} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">{deploymentUrl}</a>
                    </li>
                  </ul>
                </div>
              )}

              {error && (
                <div className="mt-6 bg-red-900/20 border border-red-500/30 rounded-lg p-4">
                  <h3 className="font-bold text-red-400 mb-2">Deployment Failed</h3>
                  <p className="text-sm text-gray-300">{error}</p>
                </div>
              )}
            </Card>
          )}
        </div>
      </main>
      
      <Footer />
    </div>
  );
};

export default Deployment;