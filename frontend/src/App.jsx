import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppProvider } from "./context/AppContext";
import Layout from "./components/Layout";

// Pages
import Landing from "./pages/Landing";
import PatientIntake from "./pages/PatientIntake";
import Transcript from "./pages/Transcript";
import Translation from "./pages/Translation";
import ClinicalSummary from "./pages/ClinicalSummary";
import DoctorDashboard from "./pages/DoctorDashboard";
import DoctorReport from "./pages/DoctorReport";
import Settings from "./pages/Settings";
import About from "./pages/About";

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/intake" element={<PatientIntake />} />
            <Route path="/transcript" element={<Transcript />} />
            <Route path="/translation" element={<Translation />} />
            <Route path="/summary" element={<ClinicalSummary />} />
            <Route path="/dashboard" element={<DoctorDashboard />} />
            <Route path="/report" element={<DoctorReport />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </Layout>
      </AppProvider>
    </BrowserRouter>
  );
}
