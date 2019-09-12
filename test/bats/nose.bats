#!/usr/bin/env bats
setup() {
    rm -rf test/.cache.tmp
}

@test "run nosetests" {
    nosetests test/nose
    run nosetests test/nose
    
    [ "$status" = 0 ]
}
