package auth
import ("errors"; "strings")
// ValidateBearer is a placeholder. Use a vetted JWT library, issuer/audience checks,
// key rotation, expiry validation, and authorization policies before production use.
func ValidateBearer(header string) (string,error) {
 parts:=strings.SplitN(header," ",2)
 if len(parts)!=2 || !strings.EqualFold(parts[0],"Bearer") || strings.TrimSpace(parts[1])=="" { return "",errors.New("missing bearer token") }
 return "",errors.New("JWT verification is not configured")
}
