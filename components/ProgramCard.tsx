import React from 'react';

interface ProgramCardProps {
  title: string;
  description: string;
  link: string;
  imageSrc: string;
}

// Fix: Changed component to be of type React.FC to correctly handle React-specific props like `key`.
const ProgramCard: React.FC<ProgramCardProps> = ({ title, description, link, imageSrc }) => {
    return (
        <a 
            href={link} 
            target={link.startsWith('#') ? '_self' : '_blank'} 
            rel="noopener noreferrer" 
            className="group block bg-brain-navy rounded-lg overflow-hidden shadow-lg hover:-translate-y-2 transition-transform duration-300"
        >
            <div className="h-48 overflow-hidden">
              <img src={imageSrc} alt={title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
            </div>
            <div className="p-6">
              <h3 className="text-xl font-bold text-brain-lightest-slate mb-2 group-hover:text-brain-teal transition-colors duration-300">{title}</h3>
              <p className="text-brain-slate">{description}</p>
            </div>
        </a>
    );
};

export default ProgramCard;
