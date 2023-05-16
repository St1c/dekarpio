import { SimulationJson } from './simulation-json';

export interface ConfigEntity {
    id: number;
    user_id: number;
    name: string;
    settings: SimulationJson;
    created_at?: string;
}