import React from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom';
import './App.css';
import FileUpload from './pages/FileUpload';
import ProjectForm from './pages/ProjectForm';
import RateLookup from './pages/RateLookup';
import ConceptEstimatePage from './pages/ConceptEstimatePage';

function App() {
  return (
    <BrowserRouter>
      <div>
        <header className="header">
          <div className="container">
            <h1>NZ Construction Pricing Engine</h1>
            <nav className="nav">
              <Link to="/upload" className="nav-link">File Upload</Link>
              <Link to="/project" className="nav-link">Create Project</Link>
              <Link to="/rates" className="nav-link">Rate Lookup</Link>
              <Link to="/estimate" className="nav-link">Concept Estimate</Link>
            </nav>
          </div>
        </header>
        
        <main className="container">
          <Routes>
            <Route path="/" element={<Navigate to="/upload" replace />} />
            <Route path="/upload" element={<FileUpload />} />
            <Route path="/project" element={<ProjectForm />} />
            <Route path="/rates" element={<RateLookup />} />
            <Route path="/estimate" element={<ConceptEstimatePage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
