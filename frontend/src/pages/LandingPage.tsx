import React from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';

const LandingPage: React.FC = () => (
  <div className="min-h-screen bg-gray-50">
    <Navbar />
    <div className="relative overflow-hidden">
      <div className="max-w-7xl mx-auto">
        <div className="relative z-10 pb-8 bg-gray-50 sm:pb-16 md:pb-20 lg:max-w-2xl lg:w-full lg:pb-28 xl:pb-32">
          <main className="mt-10 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8 xl:mt-28">
            <div className="sm:text-center lg:text-left">
              <h1 className="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
                <span className="block xl:inline">Stop wasting time in</span>{' '}
                <span className="block text-primary-600 xl:inline">endless meetings</span>
              </h1>
              <p className="mt-3 text-base text-gray-500 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0">
                Corporate employees spend 4 hours daily in back-to-back meetings. Replace status calls with AI-powered summaries optimized for Indian accents and business context.
              </p>
              <div className="mt-5 sm:mt-8 sm:flex sm:justify-center lg:justify-start">
                <div className="rounded-md shadow">
                  <Link to="/signup" className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 md:py-4 md:text-lg">Get Started</Link>
                </div>
                <div className="mt-3 sm:mt-0 sm:ml-3">
                  <Link to="/login" className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200 md:py-4 md:text-lg">Sign In</Link>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>

    <div className="py-12 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="lg:text-center">
          <h2 className="text-base text-primary-600 font-semibold tracking-wide uppercase">Features</h2>
          <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">Transform meetings into knowledge</p>
        </div>
        <div className="mt-10 grid grid-cols-1 gap-10 sm:grid-cols-2 lg:grid-cols-3">
          <FeatureCard title="AI Transcription" description="Whisper-powered transcription optimized for Indian accents and business terminology." icon="🎤" />
          <FeatureCard title="Smart Highlights" description="Automatically extract decisions, action items, and key insights from every meeting." icon="✨" />
          <FeatureCard title="Conversational Q&A" description="Ask questions about any meeting and get instant, accurate answers from the transcript." icon="💬" />
          <FeatureCard title="Vector Search" description="Qdrant-powered semantic search finds relevant context across all your meetings." icon="🔍" />
          <FeatureCard title="Export & Share" description="Download highlights as PDF, DOCX, or TXT to share with your team." icon="📄" />
          <FeatureCard title="Secure & Private" description="Per-meeting data isolation ensures your conversations stay private." icon="🔒" />
        </div>
      </div>
    </div>
  </div>
);

interface FeatureCardProps { title: string; description: string; icon: string; }
const FeatureCard: React.FC<FeatureCardProps> = ({ title, description, icon }) => (
  <div className="relative p-6 bg-gray-50 rounded-lg hover:shadow-md transition">
    <div className="text-4xl mb-4">{icon}</div>
    <h3 className="text-lg font-medium text-gray-900">{title}</h3>
    <p className="mt-2 text-base text-gray-500">{description}</p>
  </div>
);

export default LandingPage;
