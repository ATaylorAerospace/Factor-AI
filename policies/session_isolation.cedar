// Factor — Session Isolation Policy
// Ensures agent sessions are isolated per user.

forbid (
    principal,
    action == Action::"access_session",
    resource
) unless {
    resource.session_owner == principal.user_id
};

forbid (
    principal,
    action == Action::"read_trace",
    resource
) unless {
    resource.session_owner == principal.user_id
};

forbid (
    principal,
    action == Action::"export_report",
    resource
) unless {
    resource.session_owner == principal.user_id
};

// Agents can only access knowledge base in read-only mode
permit (
    principal,
    action == Action::"search_knowledge",
    resource
) when {
    resource.type == "synthetic_knowledge_base"
};
