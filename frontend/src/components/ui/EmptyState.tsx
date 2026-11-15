import React from 'react';
import { Inbox } from 'lucide-react';
import { Button } from './Button';

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode | { label: string; onClick: () => void };
}

export function EmptyState({ title, description, icon, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="text-gray-300 mb-4">
        {icon || <Inbox size={48} />}
      </div>
      <h3 className="text-lg font-medium text-gray-700 mb-1">{title}</h3>
      {description && <p className="text-gray-500 text-sm mb-4">{description}</p>}
      {action && (
        React.isValidElement(action) ? (
          action
        ) : typeof action === 'object' && 'label' in action ? (
          <Button variant="primary" onClick={action.onClick}>
            {action.label}
          </Button>
        ) : null
      )}
    </div>
  );
}
