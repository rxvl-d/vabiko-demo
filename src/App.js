import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from './components/Header';
import ArchiveBrowser from './components/ArchiveBrowser';
import PeopleBrowser from './components/PeopleBrowser';
import PersonLinking from './components/PersonLinking';
import FaceLinking from './components/FaceLinking';
import FaceSimilarity from './components/FaceSimilarity';

function App() {
  const [interfaces, setInterfaces] = useState([]);
  const [selectedInterface, setSelectedInterface] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInterfaces();
  }, []);

  const fetchInterfaces = async () => {
    try {
      const response = await axios.get('/api/interfaces');
      setInterfaces(response.data);
      if (response.data.length > 0) {
        setSelectedInterface(response.data[0].id);
      }
    } catch (error) {
      console.error('Error fetching interfaces:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-5 text-gray-600">Loading...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto p-5 bg-gray-50 min-h-screen">
      <Header 
        interfaces={interfaces}
        selectedInterface={selectedInterface}
        setSelectedInterface={setSelectedInterface}
      />

      {selectedInterface === 'archive_browser' && <ArchiveBrowser />}
      {selectedInterface === 'people_browser' && <PeopleBrowser />}
      {selectedInterface === 'person_linking' && <PersonLinking />}
      {selectedInterface === 'face_linking' && <FaceLinking />}
      {selectedInterface === 'face_similarity' && <FaceSimilarity />}
    </div>
  );
}


export default App;