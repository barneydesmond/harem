RSYNC_OPTIONS :=	--verbose \
		--checksum \
		--recursive \
		--links \
		--times \
		--perms \
		--cvs-exclude \
		--compress \
		--rsh=ssh \
		--exclude-from=NOROLLOUT \
		--filter=P_supervise \
		--delete --delete-after --delete-excluded
SAFE_RSYNC_OPTIONS = --dry-run $(RSYNC_OPTIONS)


ROHOST = shimako.meidokon.net
ROUSER = meidokonfrontend
RODIR = ~/public_html



.PHONY: all rollout safe_rollout clean update committed out

all:

clean:
	-rm -f svn-commit*.tmp
	find . \( -name '*~' -o -name '.*~' \) -exec rm -f {} \;

tidy:
	-rm -f *.pyc

update:
	svn up
	@if svn st | grep -q ^C ; then\
		echo "\\033[1;31m"; \
		echo "  ****************";\
		echo "  conflicts exist!";\
		echo "  ****************";\
		echo "\\033[0;39m"; \
		false;\
	fi

committed:
	@if [ `svn st | wc -l` -gt 0 ]; then\
		echo "\\033[1;31m"; \
		echo "  ********************************************";\
		echo "  Whoa there cowboy! You still have modified files"; \
		echo "  not commited to subversion!";\
		echo "  ********************************************";\
		echo "\\033[0;39m"; \
		svn st; \
		false;\
	fi

out: rollout
rollout: update committed
	rsync $(RSYNC_OPTIONS) \
		. \
		$(ROUSER)@$(ROHOST):$(RODIR)/
	@echo "running deploy"
	~/deploy_fixup.sh
	@echo "done"
	@echo "\\033[1;32m"
	@echo "  ============================================"
	@echo -n "  Rollout time is "
	@date
	@echo "  ============================================"
	@echo
	@if [ `svn st | wc -l` -gt 0 ]; then\
		echo "\\033[1;31m"; \
		echo "  ********************************************";\
		echo "  you still have modified files not checked in";\
		echo "  ********************************************";\
	fi
	@echo "\\033[0;39m";

safe_out: safe_rollout
safe_rollout:
	rsync $(SAFE_RSYNC_OPTIONS) \
		. \
		$(ROUSER)@$(ROHOST):$(RODIR)/
	@echo "running deploy"
	~/deploy_fixup.sh
	@echo "done"
	@echo "\\033[1;32m"
	@echo "  ============================================"
	@echo -n "  Rollout time is "
	@date
	@echo "  ============================================"
	@echo
	@if [ `svn st | wc -l` -gt 0 ]; then\
		echo "\\033[1;31m"; \
		echo "  ********************************************";\
		echo "  you still have modified files not checked in";\
		echo "  ********************************************";\
	fi
	@echo "\\033[0;39m";

