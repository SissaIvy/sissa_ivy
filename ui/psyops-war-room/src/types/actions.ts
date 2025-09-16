export type ActionStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'SUCCEEDED'
  | 'FAILED'
  | 'CANCELED';

export type ActionEvent = {
  id: string;
  status: ActionStatus;
  ts: string;        // ISO timestamp
  message?: string;
};

export type ActionTask = {
  id: string;
  startedAt: string;
  events: ActionEvent[];
  status: ActionStatus;
};
