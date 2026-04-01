import React, { useEffect, useState } from 'react';
import { meetingsApi, chatApi, highlightsApi } from '../services/api';
import { Meeting, ChatMessage } from '../types';
import Navbar from '../components/Navbar';

const DashboardPage: React.FC = () => {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [highlights, setHighlights] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'highlights' | 'chat'>('highlights');

  useEffect(() => { loadMeetings(); }, []);
  useEffect(() => { if (selectedMeeting) { loadHighlights(); loadChatHistory(); } }, [selectedMeeting]);

  const loadMeetings = async () => {
    try {
      const response = await meetingsApi.getAll();
      setMeetings(response.data);
      if (response.data.length > 0 && !selectedMeeting) setSelectedMeeting(response.data[0]);
    } catch (error) { console.error('Failed to load meetings:', error); }
  };

  const loadHighlights = async () => {
    if (!selectedMeeting) return;
    try { const response = await highlightsApi.get(selectedMeeting.id); setHighlights(response.data.highlights); }
    catch (error) { setHighlights(''); }
  };

  const loadChatHistory = async () => {
    if (!selectedMeeting) return;
    try { const response = await chatApi.getHistory(selectedMeeting.id); setChatHistory(response.data); }
    catch (error) { setChatHistory([]); }
  };

  const handleGenerateHighlights = async () => {
    if (!selectedMeeting) return;
    setIsLoading(true);
    try { const response = await highlightsApi.generate(selectedMeeting.id); setHighlights(response.data.highlights); }
    catch (error) { console.error('Failed to generate highlights:', error); }
    finally { setIsLoading(false); }
  };

  const handleAskQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMeeting || !question.trim()) return;
    setIsLoading(true);
    try {
      const response = await chatApi.ask(selectedMeeting.id, question);
      setChatHistory([...chatHistory, { content: question, is_user: true }, { content: response.data.answer, is_user: false }]);
      setQuestion('');
    } catch (error) { console.error('Failed to ask question:', error); }
    finally { setIsLoading(false); }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const name = prompt('Enter meeting name:') || file.name;
    setIsLoading(true);
    try { await meetingsApi.upload(file, name); loadMeetings(); }
    catch (error) { console.error('Failed to upload:', error); }
    finally { setIsLoading(false); }
  };

  const handleProcessMeeting = async (meetingId: number) => {
    setIsLoading(true);
    try { await meetingsApi.process(meetingId); loadMeetings(); }
    catch (error) { console.error('Failed to process:', error); }
    finally { setIsLoading(false); }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Your Meetings</h2>
                <label className="cursor-pointer bg-primary-600 text-white px-3 py-1 rounded text-sm hover:bg-primary-700">
                  Upload<input type="file" accept=".mp4,.mp3,.wav" className="hidden" onChange={handleFileUpload} />
                </label>
              </div>
              <div className="space-y-2">
                {meetings.map((meeting) => (
                  <div key={meeting.id} onClick={() => setSelectedMeeting(meeting)} className={`p-3 rounded cursor-pointer ${selectedMeeting?.id === meeting.id ? 'bg-primary-50 border-primary-500 border' : 'hover:bg-gray-50 border border-transparent'}`}>
                    <div className="font-medium truncate">{meeting.name}</div>
                    <div className="text-sm text-gray-500">Status: {meeting.status}</div>
                    {meeting.status === 'uploaded' && <button onClick={(e) => { e.stopPropagation(); handleProcessMeeting(meeting.id); }} className="mt-2 text-xs bg-primary-100 text-primary-700 px-2 py-1 rounded">Process</button>}
                  </div>
                ))}
                {meetings.length === 0 && <p className="text-gray-500 text-center py-4">No meetings yet</p>}
              </div>
            </div>
          </div>
          <div className="lg:col-span-2">
            {selectedMeeting ? (
              <div className="bg-white rounded-lg shadow">
                <div className="border-b">
                  <div className="flex">
                    <button onClick={() => setActiveTab('highlights')} className={`px-6 py-3 font-medium ${activeTab === 'highlights' ? 'border-b-2 border-primary-600 text-primary-600' : 'text-gray-500'}`}>Highlights</button>
                    <button onClick={() => setActiveTab('chat')} className={`px-6 py-3 font-medium ${activeTab === 'chat' ? 'border-b-2 border-primary-600 text-primary-600' : 'text-gray-500'}`}>Chat</button>
                  </div>
                </div>
                <div className="p-6">
                  {activeTab === 'highlights' ? (
                    <div>
                      <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-semibold">{selectedMeeting.name} - Highlights</h3>
                        {selectedMeeting.status === 'completed' && (
                          <div className="space-x-2">
                            <button onClick={handleGenerateHighlights} disabled={isLoading} className="bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700 disabled:opacity-50">{isLoading ? 'Generating...' : 'Generate'}</button>
                            {highlights && <a href={highlightsApi.download(selectedMeeting.id, 'pdf')} className="bg-gray-100 text-gray-700 px-4 py-2 rounded hover:bg-gray-200">Download PDF</a>}
                          </div>
                        )}
                      </div>
                      {selectedMeeting.status !== 'completed' ? <p className="text-gray-500">Meeting is still being processed...</p> : highlights ? <div className="whitespace-pre-wrap">{highlights}</div> : <p className="text-gray-500">No highlights generated yet.</p>}
                    </div>
                  ) : (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Chat about {selectedMeeting.name}</h3>
                      {selectedMeeting.status !== 'completed' ? <p className="text-gray-500">Meeting is still being processed...</p> : (
                        <>
                          <div className="h-96 overflow-y-auto border rounded p-4 mb-4 space-y-3">
                            {chatHistory.length === 0 ? <p className="text-gray-500 text-center">Ask a question about this meeting</p> : chatHistory.map((msg, idx) => (
                              <div key={idx} className={`p-3 rounded ${msg.is_user ? 'bg-primary-50 ml-8' : 'bg-gray-50 mr-8'}`}>
                                <div className="text-xs text-gray-500 mb-1">{msg.is_user ? 'You' : 'AI'}</div>
                                <div className="whitespace-pre-wrap">{msg.content}</div>
                              </div>
                            ))}
                          </div>
                          <form onSubmit={handleAskQuestion} className="flex gap-2">
                            <input type="text" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask a question..." className="flex-1 border rounded px-4 py-2" />
                            <button type="submit" disabled={isLoading || !question.trim()} className="bg-primary-600 text-white px-6 py-2 rounded hover:bg-primary-700 disabled:opacity-50">{isLoading ? '...' : 'Ask'}</button>
                          </form>
                        </>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ) : <div className="bg-white rounded-lg shadow p-12 text-center"><p className="text-gray-500">Select a meeting to view details</p></div>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
