# Deployment Checklist

## Pre-Deployment

### Code Cleanup
- [x] Remove test files (test_*.py, *_test.py)
- [x] Remove debug files (check_*.py, output_*.json)
- [x] Remove console.log statements (except console.error)
- [x] Clean database (remove test data)
- [x] Update .gitignore

### Security Review
- [x] Verify no API keys or secrets in code
- [x] Check .env is in .gitignore
- [ ] Review authentication flows
- [ ] Verify encryption implementation
- [ ] Check CORS settings for production domains

### Configuration
- [x] Set FLASK_ENV=production in .env
- [x] Generate new JWT_SECRET for production
- [x] Generate new FLASK_SECRET_KEY for production
- [x] Generate new ENCRYPTION_MASTER_KEY for production
- [x] Update CORS_ORIGINS for production domain
- [x] Configure production database URL

### Database
- [x] Run all migrations
- [ ] Create backup of any important data
- [x] Verify table creation scripts
- [x] Test database connection with SSL

### Backend
- [x] Test all API endpoints
- [x] Verify error handling
- [x] Check rate limiting
- [x] Test authentication flow
- [x] Verify encryption/decryption
- [x] Test PDF generation

### Frontend
- [ ] Build production bundle: `npm run build`
- [ ] Test production build locally
- [ ] Verify API_BASE_URL points to production
- [x] Check responsive design
- [ ] Test on multiple browsers

## Deployment Steps

### 1. Environment Variables (Vercel)
Set these in Vercel dashboard for both backend and frontend:

**Backend Environment Variables:**
```
POSTGRES_URL=<vercel-postgres-connection-string>
ENCRYPTION_MASTER_KEY=<generate-new-key>
JWT_SECRET=<generate-new-secret>
FLASK_ENV=production
FLASK_SECRET_KEY=<generate-new-secret>
TORN_API_BASE_URL=https://api.torn.com/v2
RATE_LIMIT_PER_MINUTE=80
SESSION_TIMEOUT_MINUTES=30
ACCESS_TOKEN_EXPIRY_HOURS=24
REFRESH_TOKEN_EXPIRY_DAYS=7
AUDIT_LOG_RETENTION_DAYS=30
```

**Frontend Environment Variables:**
```
REACT_APP_BACKEND_API_URL=<your-backend-vercel-url>
```

### 2. Generate Production Keys

```python
# Generate ENCRYPTION_MASTER_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate JWT_SECRET and FLASK_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 3. Deploy to Vercel

```bash
# Login to Vercel
vercel login

# Deploy
vercel --prod
```

### 4. Post-Deployment

- [ ] Test login with Torn API key
- [ ] Create test war session
- [ ] Test member synchronization
- [ ] Test payout calculation
- [ ] Test PDF export
- [ ] Verify audit logging
- [ ] Test user management
- [ ] Check error handling
- [ ] Monitor logs for issues

## Production Monitoring

### Health Checks
- [ ] Set up uptime monitoring (e.g., UptimeRobot)
- [ ] Monitor API response times
- [ ] Check database connection pool
- [ ] Monitor rate limit usage

### Logging
- [ ] Review Vercel logs regularly
- [ ] Monitor audit log table size
- [ ] Check for error patterns
- [ ] Set up alerts for critical errors

### Database
- [ ] Monitor database size
- [ ] Set up automated backups
- [ ] Check query performance
- [ ] Review audit log retention

### Security
- [ ] Review CORS settings
- [ ] Check authentication logs
- [ ] Monitor failed login attempts
- [ ] Review API rate limiting

## Maintenance

### Weekly
- [ ] Review error logs
- [ ] Check database size
- [ ] Monitor API usage

### Monthly
- [ ] Review audit logs before archival
- [ ] Check database backups
- [ ] Update dependencies (security patches)
- [ ] Review user access logs

### Quarterly
- [ ] Full security audit
- [ ] Performance review
- [ ] Database optimization
- [ ] Update dependencies (major versions)

## Rollback Plan

If deployment fails:

1. **Frontend**: Revert to previous Vercel deployment
2. **Backend**: Revert to previous Vercel deployment
3. **Database**: Restore from backup if schema changed
4. **Verify**: Test all critical features

## Support

### Common Issues

**Database Connection Issues:**
- Verify POSTGRES_URL includes `?sslmode=require`
- Check Vercel Postgres connection pool limits
- Verify SSL certificates

**Authentication Issues:**
- Verify JWT_SECRET matches between deployments
- Check CORS settings
- Verify Torn API key validity

**Rate Limiting:**
- Monitor Torn API usage
- Adjust RATE_LIMIT_PER_MINUTE if needed
- Check request queuing logic

### Contact

For issues or questions:
- Check Vercel logs first
- Review audit logs in database
- Check GitHub issues

## Notes

- **Never commit .env files**
- **Always generate new keys for production**
- **Test thoroughly before deploying to production**
- **Keep production database backed up**
- **Monitor logs after deployment**
