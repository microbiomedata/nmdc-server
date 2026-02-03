import { EnvoNode } from "./data/api";

export interface User {
    id: string,
    orcid: string;
    name: string;
    is_admin: boolean;
    email?: string;
}

export interface LoadOptionsParams {
    action: string;
    parentNode: EnvoNode | null;
    callback: (err: Error | null, data: EnvoNode[]) => void;
    searchQuery?: string;
}
