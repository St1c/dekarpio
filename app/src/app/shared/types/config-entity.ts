import { SimulationJson } from './simulation-json';

export interface ConfigEntity {
    id: number;
    user_id: number;
    name: string;
    settings: SimulationJson;
    email?: string;
    created_at?: string;
    updated_at?: string;
}