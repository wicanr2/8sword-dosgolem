package eightsword

// openOverlayReference keeps the previous overlay and its asset-specific tests
// available as an independent reference. This is a test-only fixture, never a
// player option. Spec 047 production coverage lives in source_runtime_test.go
// and the normal GUI receipts checked by audit-source-player.py.
func openOverlayReference(opt Options) (*Engine, error) {
	e, err := Open(opt)
	if err != nil || !e.sourceEnabled {
		return e, err
	}
	if e.sourceClose != nil {
		e.sourceClose()
	}
	e.sourceEnabled = false
	e.sourceInstall, e.sourceRender, e.sourceClose = nil, nil, nil
	// The production asset loader deliberately skips these legacy callbacks.
	if e.Museum != nil {
		e.Museum, err = loadIntroMuseum(e, opt.Assets, opt.Root)
		if err != nil {
			e.Close()
			return nil, err
		}
	}
	return e, nil
}
