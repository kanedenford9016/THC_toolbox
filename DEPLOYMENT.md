# Deployment Checklist

## Pre-Deployment

### 1. Environment Setup
- [ ] Create Vercel account
- [ ] Create Vercel Postgres database
- [ ] Copy Postgres connection string
- [ ] Generate encryption keys:
  ```python
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- [ ] Generate JWT secret (32+ character random string)
- [ ] Generate Flask secret (32+ character random string)

### 2. Vercel Configuration
- [ ] Install Vercel CLI: `npm install -g vercel`
- [ ] Login to Vercel: `vercel login`
- [ ] Link project: `vercel` (run in project root)

### 3. Environment Variables (Vercel Dashboard)
Go to Project Settings → Environment Variables and add:

#### Backend Variables
- [ ] `POSTGRES_URL` - Vercel Postgres connection string (with `?sslmode=require`)
- [ ] `ENCRYPTION_MASTER_KEY` - Generated Fernet key
- [ ] `JWT_SECRET` - Generated random string
- [ ] `FLASK_SECRET_KEY` - Generated random string
- [ ] `TORN_API_BASE_URL` - `https://api.torn.com/v2`
- [ ] `RATE_LIMIT_PER_MINUTE` - `80`

#### Frontend Variables
- [ ] `REACT_APP_BACKEND_API_URL` - Your Vercel backend URL (e.g., `https://your-project.vercel.app/api`)

**Important**: Mark all secrets as "Sensitive" to hide values in Vercel dashboard.

### 4. Database Setup
- [ ] Run migration script on Vercel Postgres:
  ```bash
  # Get connection string from Vercel
  psql "your-vercel-postgres-url" -f backend/migrations/001_initial_schema.sql
  ```

## Deployment

### 5. Deploy to Production
```bash
vercel --prod
```

### 6. Verify Deployment
- [ ] Backend health check: `https://your-project.vercel.app/api/health`
- [ ] Frontend loads: `https://your-project.vercel.app/`
- [ ] Login works with Torn API key
- [ ] Database connection successful

### 7. Configure Cron Job
- [ ] Verify cron configuration in vercel.json
- [ ] Check cron logs in Vercel dashboard after first run
- [ ] Cron runs monthly: `/api/archive/run-archival`

## Post-Deployment

### 8. Security Verification
- [ ] HTTPS enabled on all endpoints
- [ ] SSL certificate valid
- [ ] Database connection uses SSL
- [ ] CORS configured correctly
- [ ] Rate limiting active
- [ ] Sensitive data encrypted in database

### 9. Testing
- [ ] Test login with valid faction admin API key
- [ ] Test login rejection for non-admin users
- [ ] Create test war session
- [ ] Refresh members from Torn API
- [ ] Calculate payouts
- [ ] Add bonuses to members
- [ ] Add other payments
- [ ] Export PDF report
- [ ] Complete war session
- [ ] View history
- [ ] Access archive logs

### 10. Monitoring Setup (Optional)
- [ ] Set up error tracking (Sentry, Rollbar, etc.)
- [ ] Configure uptime monitoring
- [ ] Set up log aggregation
- [ ] Create backup strategy for database

## Common Issues & Solutions

### Issue: Database Connection Failed
**Solution**: Ensure `POSTGRES_URL` includes `?sslmode=require` and SSL certificates are valid.

### Issue: Frontend Cannot Reach Backend
**Solution**: Verify `REACT_APP_BACKEND_API_URL` is set correctly and includes `/api` path.

### Issue: Torn API Authentication Failed
**Solution**: 
1. Verify user has faction admin permissions (Leader, Co-leader, or Officer)
2. Check API key is valid and not expired
3. Ensure `TORN_API_BASE_URL` is `https://api.torn.com/v2`

### Issue: Encryption Errors
**Solution**: Regenerate `ENCRYPTION_MASTER_KEY` and restart application. Note: This will invalidate existing encrypted data.

### Issue: Rate Limiting Too Aggressive
**Solution**: Adjust `RATE_LIMIT_PER_MINUTE` environment variable (default: 80).

### Issue: Session Expires Too Quickly
**Solution**: Adjust in `backend/config/settings.py`:
- `SESSION_TIMEOUT_MINUTES` (default: 30)
- `ACCESS_TOKEN_EXPIRY_HOURS` (default: 24)
- `REFRESH_TOKEN_EXPIRY_DAYS` (default: 7)

## Maintenance

### Regular Tasks
- [ ] Monthly: Review audit logs
- [ ] Monthly: Verify archival cron ran successfully
- [ ] Quarterly: Review and rotate encryption keys (requires data migration)
- [ ] Quarterly: Update dependencies
- [ ] As needed: Backup database

### Updating the Application
```bash
# Make changes locally
git add .
git commit -m "Description of changes"
git push

# Deploy to production
vercel --prod
```

## Rollback Procedure
If deployment fails or issues occur:

1. **Quick Rollback** (Vercel Dashboard):
   - Go to Deployments
   - Find last stable deployment
   - Click "..." → "Promote to Production"

2. **Manual Rollback**:
   ```bash
   # Revert to previous commit
   git revert HEAD
   git push
   vercel --prod
   ```

## Support Contacts
- Torn API Support: https://www.torn.com/forums.php#/p=threads&f=2
- Vercel Support: https://vercel.com/support
- PostgreSQL Documentation: https://www.postgresql.org/docs/

## Notes
- All times are in UTC
- Audit logs retained for 30 days before archival
- Archived logs are read-only
- PDF exports generated on-demand
- Rate limit applies globally across all users
