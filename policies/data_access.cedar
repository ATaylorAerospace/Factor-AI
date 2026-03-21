// Factor — Data Access Policy
// Enforces session isolation: users can only access their own documents.

forbid (
    principal,
    action == Action::"read_document",
    resource
) unless {
    resource.session_owner == principal.user_id
};

forbid (
    principal,
    action == Action::"write_document",
    resource
) unless {
    resource.session_owner == principal.user_id
};

forbid (
    principal,
    action == Action::"delete_document",
    resource
) unless {
    resource.session_owner == principal.user_id
};

// Allow health check and public endpoints for all authenticated users
permit (
    principal,
    action == Action::"read_public",
    resource
);
